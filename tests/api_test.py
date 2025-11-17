#!/usr/bin/env python3
import io
import os
from hashlib import sha256
from pickle import dumps

from rbloom import Bloom


def hash_func(obj):
    """Convert arbitrary objects to i128 integers for hashing."""
    h = sha256(dumps(obj)).digest()
    return int.from_bytes(h[:16], "big", signed=True)


def test_bloom(bloom: Bloom):
    assert not bloom
    assert bloom.approx_items == 0.0

    bloom.add(hash_func('foo'))
    assert bloom
    assert bloom.approx_items > 0.0

    bloom.add(hash_func('bar'))

    assert hash_func('foo') in bloom
    assert hash_func('bar') in bloom
    assert hash_func('baz') not in bloom

    bloom.update([hash_func('baz'), hash_func('qux')])
    assert hash_func('baz') in bloom
    assert hash_func('qux') in bloom

    other = bloom.copy()
    assert other == bloom
    assert other is not bloom

    other.clear()
    assert not other
    assert other.approx_items == 0.0

    other.update([hash_func('foo'), hash_func('bar'), hash_func('baz'), hash_func('qux')])
    assert other == bloom

    other.update(hash_func(str(i).encode()*500) for i in range(100000))
    for i in range(100000):
        assert hash_func(str(i).encode()*500) in other
    assert bloom != other
    assert bloom & other == bloom
    assert bloom | other == other

    bloom &= other
    assert bloom < other

    orig = bloom.copy()
    bloom |= other
    assert bloom == other
    assert bloom > orig
    assert bloom >= orig
    assert bloom.issuperset(other)
    assert orig <= bloom
    assert orig.issubset(bloom)
    assert bloom >= bloom
    assert bloom.issuperset(bloom)
    assert bloom <= bloom
    assert bloom.issubset(bloom)

    bloom = orig.copy()
    bloom.update(other)
    assert bloom == other
    assert bloom > orig

    bloom = orig.copy()
    assert other == bloom.union(other)
    assert bloom == bloom.intersection(other)

    bloom.intersection_update(other)
    assert bloom == orig

    # TEST FILE PERSISTENCE
    i = 0
    while os.path.exists(f'test{i}.bloom'):
        i += 1
    filename = f'test{i}.bloom'

    try:
        # save and load from file path
        bloom.save(filename)
        bloom2 = Bloom.load(filename)
        assert bloom == bloom2
    finally:
        # remove the file
        os.remove(filename)

    # TEST FILE OBJECT PERSISTENCE
    buffer = io.BytesIO()
    bloom.save(buffer)
    buffer.seek(0)
    bloom3 = Bloom.load(buffer)
    assert bloom == bloom3

    # TEST bytes PERSISTENCE
    bloom_bytes = bloom.save_bytes()
    assert type(bloom_bytes) == bytes
    bloom4 = Bloom.load_bytes(bloom_bytes)
    assert bloom == bloom4


def operations_with_self():
    bloom = Bloom(1000, 0.1)
    bloom.add(hash_func('foo'))
    assert hash_func('foo') in bloom
    bloom |= bloom
    bloom &= bloom
    bloom.update(bloom)
    bloom.update(bloom, bloom)
    bloom.update(bloom, [hash_func('bob')], bloom)
    assert hash_func('foo') in bloom
    assert hash_func('bob') in bloom

    bloom.intersection_update(bloom)
    bloom.intersection_update(bloom, bloom)
    bloom.intersection_update(bloom, [hash_func('foo')], bloom)
    assert hash_func('foo') in bloom
    assert hash_func('bob') not in bloom
    assert bloom == bloom
    assert bloom <= bloom
    assert bloom >= bloom
    assert not (bloom > bloom)
    assert not (bloom < bloom)
    assert bloom.issubset(bloom)
    assert bloom.issuperset(bloom)
    assert bloom.union(bloom) == bloom
    assert bloom.union(bloom, bloom) == bloom
    assert bloom.intersection(bloom) == bloom
    assert bloom.intersection(bloom, bloom) == bloom


def api_suite():
    assert repr(Bloom(27_000, 0.0317)) == "<Bloom size_in_bits=193960 approx_items=0.0>"

    test_bloom(Bloom(13242, 0.0000001))
    test_bloom(Bloom(9874124, 0.01))
    test_bloom(Bloom(2837, 0.5))

    operations_with_self()

    print('All API tests passed')


if __name__ == '__main__':
    api_suite()
