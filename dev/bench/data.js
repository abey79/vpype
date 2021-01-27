window.BENCHMARK_DATA = {
  "lastUpdate": 1611790445417,
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
      },
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
          "id": "4e50480bfbd34c40b01ab71f008cae8370b8a81a",
          "message": "Add continuous benchmarking setup",
          "timestamp": "2021-01-27T15:08:51Z",
          "url": "https://github.com/abey79/vpype/pull/184/commits/4e50480bfbd34c40b01ab71f008cae8370b8a81a"
        },
        "date": 1611790444526,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/300_beziers.svg]",
            "value": 1.136498110694519,
            "unit": "iter/sec",
            "range": "stddev: 0.023485558111833896",
            "extra": "mean: 879.8958754000001 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/900_quad_beziers.svg]",
            "value": 0.8365144375468091,
            "unit": "iter/sec",
            "range": "stddev: 0.02118901199998302",
            "extra": "mean: 1.1954366298 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/500_circles.svg]",
            "value": 1.081620783659363,
            "unit": "iter/sec",
            "range": "stddev: 0.02842038409734994",
            "extra": "mean: 924.5384474000012 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/500_polylines.svg]",
            "value": 0.7937252430627824,
            "unit": "iter/sec",
            "range": "stddev: 0.03546186424467226",
            "extra": "mean: 1.2598818152000006 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_read[benchmark/bar_nodef_path_polylines.svg]",
            "value": 0.29955987185000266,
            "unit": "iter/sec",
            "range": "stddev: 0.034813449895696395",
            "extra": "mean: 3.3382308312000006 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_linesort",
            "value": 0.4962054181249973,
            "unit": "iter/sec",
            "range": "stddev: 0.02607490144945229",
            "extra": "mean: 2.0152943991999974 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_linemerge",
            "value": 0.2697253051334297,
            "unit": "iter/sec",
            "range": "stddev: 0.018968360958063857",
            "extra": "mean: 3.7074756464000016 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}