from bot.utils import formatting

def test_truncate1():
    assert formatting.truncate(1.001,2) == 1.00

def test_truncate2():
    assert formatting.truncate(1.2345,4) == 1.2345

def test_truncate3():
    assert formatting.truncate(1.23456,0) == 1
