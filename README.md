
# VPSim

VPSim is a digital architecture design environment used to speed up design space exploration (DSE) through simulation and rapid validation. 
Users can model a complex memory hierarchy and estimate its performance, for example, thanks to a wide variety of available processor and device models.

[VPSim](https://list.cea.fr/en/page/vpsim-explore-simulate-and-validate-complex-electronic-architectures)

# Installation

## Requirements
- To build VPSim & the modified QEMU on a fresh Ubuntu 22.04 LTS installation, you will need to install these libraries:

    ```sh
    apt install -y pkg-config libglib2.0-dev libpixman-1-dev ninja-build python
    ```

Now your environment is set, please follow the following steps:

## Clone & Build (deprecated)
1. Clone this git repository and update its submodules:

    ```sh
    git clone git@github.com:CEA-LIST/VPSim.git
    cd VPSim
    git submodule init
    git submodule update --recursive
    ```

2. Build targets and copy artifacts to the release directory [VPSim/vpsim-release](https://github.com/CEA-LIST/vpsim-release.git) sub-directory:

    to do so, we configured a custom command in CMakeLists that rename and copy the targets to the appropriate folder in the release test environment
    ```sh
    mkdir build && cd build
    cmake ..
    make all -j
    cd ../
    ```

# Getting to test VPSim and run your first simulation (deprecated)
- To try VPSim and customize your architecture to simulate, please follow the `README.md` file in the following sub-directory:
  - [VPSim/vpsim-release](https://github.com/CEA-LIST/vpsim-release.git)


# Run tests

It is possible to run a batchs of bare-metal tests over a few platforms.

```
make test
```

## VPSIM SystemC tests

```
ctest --test-dir ./debug --tests-regex vpsim[.]unittest
```

if a test fails :
```

98% tests passed, 1 tests failed out of 48

Total Test time (real) =   0.27 sec

The following tests FAILED:
         23 - vpsim.unittest.Logger.writeGlobalLogMacro (Failed)
```

You can easily rerun the specific test with ` --rerun-failed --output-on-failure` extra arguments : 

```
ctest --test-dir ./release/ --tests-regex vpsim.unittest.Logger.writeGlobalLogMacro --output-on-failure
```

## VPSIM use-case tests

```
ctest --test-dir ./debug --tests-regex "vpsim[.]run_*" -VV
```

To rerun the test : 

```
ctest --test-dir ./debug/ --tests-regex vpsim.run_simple_qemu_9_with_kernel_testcase_sesam_013_benchmark_small_float_sve_run --output-on-failure

```
