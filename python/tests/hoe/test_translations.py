from hoe import translations


MOVE = 4 * translations.UP + 4 * translations.RIGHT


def test_move_when_all_wrap():
    pos = translations.move((0, 0), MOVE, (2, 5), [False, False])
    assert (pos == (0, 4)).all()


def test_move_when_all_clip():
    pos = translations.move((0, 0), MOVE, (2, 5), [True, True])
    assert (pos == (2, 4)).all()


def test_move_when_clip_and_wrap():
    pos = translations.move((0, 0), MOVE, (2, 5), [True, False])
    assert (pos == (2, 4)).all()
