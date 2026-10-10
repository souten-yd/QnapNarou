import unittest
from tools.io_probe import parse_diskstats, rates


class DiskProbeTests(unittest.TestCase):
    def test_writes_and_busy_are_differences_not_absolute(self):
        a = parse_diskstats("8 0 sda 10 0 100 0 20 0 100 0 0 200 0 0")
        b = parse_diskstats("8 0 sda 10 0 100 0 30 0 2100 0 0 300 0 0")
        values = rates(a, b, 10)["sda"]
        self.assertEqual(values["write_iops"], 1)
        self.assertEqual(values["write_mib_s"], round(2000 * 512 / (1048576 * 10), 4))
        self.assertEqual(values["busy_percent"], 1)

    def test_counter_reset_skipped(self):
        a = parse_diskstats("8 0 sda 10 0 100 0 20 0 100 0 0 200 0 0")
        b = parse_diskstats("8 0 sda 10 0 100 0 2 0 10 0 0 20 0 0")
        self.assertEqual(rates(a, b, 10), {})

    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            rates({}, {}, 0)


if __name__ == "__main__":
    unittest.main()
