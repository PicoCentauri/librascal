#include <benchmark/benchmark.h>
#include <functional>

#include "math/interpolator.hh"
#include "representations/representation_manager_spherical_expansion.hh"



using namespace rascal::math;

namespace rascal {
  namespace internal {

    // TODO(alex) To have a credible time benchmarks for the initialzation function.
    // distance function caluclates for (radial_max, angular_max+1) points, this must be incuded
    // in the intp, maybe make extra class MatrixIntp

    static void BM_RadialContr(benchmark::State& state) {
      int max_radial{20};
      int max_angular{max_radial-1};
      json fc_hypers{
           {"type", "Constant"},
           {"gaussian_sigma", {{"value", 0.5}, {"unit", "A"}}}
          };
      json hypers{{"gaussian_density", fc_hypers},
                {"max_radial", max_radial},
                {"max_angular", max_angular},
                {"cutoff_function", {{"cutoff",{{"value", 2.0}, {"unit", "A"}}}}}
      };
      auto radial_contr{RadialContribution<RadialBasisType::GTO>(hypers)};
      math::Vector_t points = math::Vector_t::LinSpaced(3000,0,5);
      for (auto _ : state) {
        for (int i{0}; i<points.size();i++) {
          radial_contr.compute_contribution<AtomicSmearingType::Constant>(points(i), 0.5)(0,17);
        }
      }
    }
    BENCHMARK(BM_RadialContr);

    static void BM_RadialContrIntp(benchmark::State& state) {
    auto intp{RadialContrInterpolator <
      InterpolationMethod<InterpolationMethod_t::CubicSpline>,
      GridRational<GridType_t::Uniform, RefinementMethod_t::Adaptive>,
      SearchMethod<SearchMethod_t::Hunt>
        >()};
      math::Vector_t points = math::Vector_t::LinSpaced(3000,0,5);
      intp.initalize(0,17, 0,5, 1e-10); 
      for (auto _ : state) {
        for (int i{0}; i<points.size();i++) {
          intp.interpolate(points(i));
        }
      }
    }
    BENCHMARK(BM_RadialContrIntp);
    // 100 times slower than with precompution that is why we skip
    //static double radial_contr_function_generator(int n, int l, double r) {

    //  int max_radial{20};
    //  int max_angular{max_radial-1};
    //  json fc_hypers{
    //       {"type", "Constant"},
    //       {"gaussian_sigma", {{"value", 0.5}, {"unit", "A"}}}
    //      };
    //  json hypers{{"gaussian_density", fc_hypers},
    //            {"max_radial", max_radial},
    //            {"max_angular", max_angular},
    //            {"cutoff_function", {{"cutoff",{{"value", 2.0}, {"unit", "A"}}}}}
    //  };
    //  auto radial_contr{RadialContribution<RadialBasisType::GTO>(hypers)};
    //  return radial_contr.compute_contribution<AtomicSmearingType::Constant>(r, 0.5)(n,l);
    //}
    //static void BM_RadialContrFunc(benchmark::State& state) {
    //  std::function<double(double)> func{std::bind(radial_contr_function_generator, 0, 17, std::placeholders::_1)};
    //  math::Vector_t points = math::Vector_t::LinSpaced(3000,0,5);
    //  for (auto _ : state) {
    //    for (int i{0}; i<points.size();i++) {
    //      func(points(i));
    //    }
    //  }
    //}
    // Register the function as a benchmark
    //BENCHMARK(BM_RadialContrFunc);
  }
}

BENCHMARK_MAIN();
