import datetime
import shutil
import unittest

from lib.winner_repository import save, find_all


class WinnerRepositoryTest(unittest.TestCase):
    def tearDown(self):
        shutil.rmtree('database')

    def test_save(self):
        save(dict(name="Verbeast", date=datetime.datetime(2020, 5, 17)))
        with open("database/winner/2020-05-17.json", "r") as f:
            self.assertEqual(f.read(), '{"name": "Verbeast", "date": "2020-05-17"}')

    def test_find_all(self):
        save(dict(name="Verbeast", date=datetime.datetime(2020, 5, 17)))
        victories = find_all()
        self.assertEqual(victories, [dict(name="Verbeast", date=datetime.datetime(2020, 5, 17))])


if __name__ == '__main__':
    unittest.main()
