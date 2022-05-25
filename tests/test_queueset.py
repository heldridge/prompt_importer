from prompt_importer import queueset


def test_keeps_size():
    q = queueset.QueueSet(3)
    q.push("a")
    q.push("b")
    q.push("c")
    q.push("d")
    q.push("e")
    assert list(q) == ["e", "d", "c"]


def test_bumps_to_front():
    q = queueset.QueueSet(4)
    q.push("a")
    q.push("b")
    q.push("a")

    assert list(q) == ["a", "b"]
