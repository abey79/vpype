window.BENCHMARK_DATA = {
  "lastUpdate": 1611786306086,
  "repoUrl": "https://github.com/abey79/vpype",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "name": "abey79",
            "username": "abey79"
          },
          "committer": {
            "name": "abey79",
            "username": "abey79"
          },
          "id": "12e6c848dc29bdeb200ca30a4af82a1bb8f7bb2a",
          "message": "Add continuous benchmarking setup",
          "timestamp": "2021-01-27T15:08:51Z",
          "url": "https://github.com/abey79/vpype/pull/184/commits/12e6c848dc29bdeb200ca30a4af82a1bb8f7bb2a"
        },
        "date": 1611786305413,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/300_beziers.svg]",
            "value": 1.0316861743786325,
            "unit": "iter/sec",
            "range": "stddev: 0.06686184985716483",
            "extra": "mean: 969.2870029999999 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/900_quad_beziers.svg]",
            "value": 0.7629394721006981,
            "unit": "iter/sec",
            "range": "stddev: 0.10313277126795677",
            "extra": "mean: 1.3107199673999996 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/500_circles.svg]",
            "value": 1.0427901898903058,
            "unit": "iter/sec",
            "range": "stddev: 0.036514547677462025",
            "extra": "mean: 958.9656766000004 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/500_polylines.svg]",
            "value": 0.7789855509570618,
            "unit": "iter/sec",
            "range": "stddev: 0.021631143593755772",
            "extra": "mean: 1.283720858200001 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/bar_nodef_path_polylines.svg]",
            "value": 0.26208471081475515,
            "unit": "iter/sec",
            "range": "stddev: 0.282679597682261",
            "extra": "mean: 3.815560232 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}