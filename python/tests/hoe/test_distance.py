from hoe import distance


def test_pixels_per_frame():
    for j in range(100):
        assert j == sum(distance.pixels_per_frame(j, i, 30) for i in range(30))
