import unittest
from tools.io_probe import parse_diskstats, rates

class DiskProbeTests(unittest.TestCase):
    def test_correct_sector_and_io_rates(self):
        a = parse_diskstats("8 0 sda 10 0 100 0 20 0 100 0 0 200 0 0")
        b = parse_diskstats("8 0 sda 12 0 1100 0 30 0 2100 0 0 300 0 0")
        actual = rates(a, b, 10)["sda"]
        self.assertEqual(actual["read_iops"], 0.2)
        self.assertEqual(actual["write_iops"], 1)
        self.assertEqual(actual["read_mib_s"], round(1000 * 512 / (1048576 * 10), 4))
        self.assertEqual(actual["write_mib_s"], round(2000 * 512 / (1048576 * 10), 4))
        self.assertEqual(actual["busy_percent"], 1)

    def test_counter_reset_fail_closed(self):
        a = parse_diskstats("8 0 sda 10 0 100 0 20 0 100 0 0 200 0 0")
        b = parse_diskstats("8 0 sda 10 0 100 0 2 0 10 0 0 20 0 0")
        self.assertEqual(rates(a, b, 10), {})

    def test_bad_duration(self):
        with self.assertRaises(ValueError):
            rates({}, {}, 0)

    def test_skip_short_and_non_numeric_and_negative(self):
        sample = "8 0 sda 10 0 100 0 20 0 100 0 0 200 0 0\n8 0 sdb no 0 100 0 20 0 100 0 0 200 0 0\n8 0 sdc -1 0 100 0 20 0 100 0 0 200 0 0\ninvalid"
        self.assertEqual(set(parse_diskstats(sample)), {"sda"})

if __name__ == "__main__":
    unittest.main()
