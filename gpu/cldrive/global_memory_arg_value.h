// Copyright (c) 2016, 2017, 2018, 2019 Chris Cummins.
// This file is part of cldrive.
//
// cldrive is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// cldrive is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with cldrive.  If not, see <https://www.gnu.org/licenses/>.
#pragma once

#include "gpu/cldrive/kernel_arg_value.h"
#include "gpu/cldrive/opencl_type.h"

#include "third_party/opencl/cl.hpp"

#include "phd/logging.h"
#include "phd/string.h"

namespace gpu {
namespace cldrive {

// TODO(cldrive): Work in progress!
template <typename T>
bool ScalarEquality(const T &lhs, const T &rhs) {
  return lhs == rhs;
}

// An array argument.
template <typename T>
class GlobalMemoryArgValue : public KernelArgValue {
 public:
  template <typename... Args>
  GlobalMemoryArgValue(size_t size, Args &&... args) : vector_(size, args...) {}

  virtual bool operator==(const KernelArgValue *const rhs) const override {
<<<<<<< HEAD:gpu/cldrive/global_memory_arg_value.h
    auto array_ptr = dynamic_cast<const GlobalMemoryArgValue *const>(rhs);
=======
    auto array_ptr = dynamic_cast<const ArrayKernelArgValue *const>(rhs);
>>>>>>> 8b16e8e86... Work in progress on cldrive vector args.:gpu/cldrive/array_kernel_arg_value.h
    if (!array_ptr) {
      return false;
    }

    if (vector().size() != array_ptr->vector().size()) {
      return false;
    }

    for (size_t i = 0; i < vector().size(); ++i) {
<<<<<<< HEAD:gpu/cldrive/global_memory_arg_value.h
      if (!opencl_type::Equal(vector()[i], array_ptr->vector()[i])) {
=======
      if (!ElementEquality(vector()[i], array_ptr->vector()[i])) {
>>>>>>> 8b16e8e86... Work in progress on cldrive vector args.:gpu/cldrive/array_kernel_arg_value.h
        return false;
      }
    }

    return true;
  }

  bool ElementEquality(const T &lhs, const T &rhs) const {
    return ScalarEquality(lhs, rhs);
  }

  virtual bool operator!=(const KernelArgValue *const rhs) const override {
    return !(*this == rhs);
  }

  std::vector<T> &vector() { return vector_; }

  const std::vector<T> &vector() const { return vector_; }

  size_t size() const { return vector().size(); }

  virtual void CopyToDevice(const cl::CommandQueue &queue,
                            ProfilingData *profiling) override {
    CHECK(false);
  }

  virtual std::unique_ptr<KernelArgValue> CopyFromDevice(
      const cl::CommandQueue &queue, ProfilingData *profiling) override {
    CHECK(false);
    return std::unique_ptr<KernelArgValue>(nullptr);
  }

  virtual void SetAsArg(cl::Kernel *kernel, size_t arg_index) override {
    CHECK(false);
  }

<<<<<<< HEAD:gpu/cldrive/global_memory_arg_value.h
  virtual string ToString() const override {
    string s = "";
    for (const auto &value : vector()) {
      absl::StrAppend(&s, opencl_type::ToString(value));
      absl::StrAppend(&s, ",");
    }
    return s;
  };

  virtual size_t SizeInBytes() const override {
    return sizeof(T) * vector_.size();
  }
=======
  virtual string ToString() const override;
>>>>>>> 8b16e8e86... Work in progress on cldrive vector args.:gpu/cldrive/array_kernel_arg_value.h

 protected:
  std::vector<T> vector_;
};

// TODO(cldrive): Work in progress!
template <typename T>
/*virtual*/ string ArrayKernelArgValue<T>::ToString() const {
  string s = "";
  for (auto &value : vector()) {
    absl::StrAppend(&s, value);
    absl::StrAppend(&s, ", ");
  }
  return s;
}

template <>
/*virtual*/ string ArrayKernelArgValue<cl_char2>::ToString() const;

template <>
/*virtual*/ bool ArrayKernelArgValue<cl_char2>::ElementEquality(
    const cl_char2 &lhs, const cl_char2 &rhs) const;

// An array value with a device-side buffer.
template <typename T>
class GlobalMemoryArgValueWithBuffer : public GlobalMemoryArgValue<T> {
 public:
  template <typename... Args>
  GlobalMemoryArgValueWithBuffer(const cl::Context &context, size_t size,
                                 Args &&... args)
      : GlobalMemoryArgValue<T>(size, args...),
        buffer_(context, /*flags=*/CL_MEM_READ_WRITE,
                /*size=*/sizeof(T) * size) {}

  cl::Buffer &buffer() { return buffer_; }

  virtual void SetAsArg(cl::Kernel *kernel, size_t arg_index) override {
    kernel->setArg(arg_index, buffer());
  }

  virtual void CopyToDevice(const cl::CommandQueue &queue,
                            ProfilingData *profiling) override {
    size_t buffer_size = this->vector().size() * sizeof(T);
    util::CopyHostToDevice(queue, this->vector().data(), buffer(), buffer_size,
                           profiling);
  }

  virtual std::unique_ptr<KernelArgValue> CopyFromDevice(
      const cl::CommandQueue &queue, ProfilingData *profiling) override {
<<<<<<< HEAD:gpu/cldrive/global_memory_arg_value.h
<<<<<<< HEAD:gpu/cldrive/global_memory_arg_value.h
    size_t buffer_size = this->vector().size() * sizeof(T);
    auto new_arg = std::make_unique<GlobalMemoryArgValue<T>>(this->size());
    util::CopyDeviceToHost(queue, buffer(), new_arg->vector().data(),
                           buffer_size, profiling);
=======
    auto new_arg =
        std::make_unique<ArrayKernelArgValue<T>>(this->size());
=======
    auto new_arg = std::make_unique<ArrayKernelArgValue<T>>(this->size());
>>>>>>> 8b16e8e86... Work in progress on cldrive vector args.:gpu/cldrive/array_kernel_arg_value.h
    CopyDeviceToHost(queue, buffer(), new_arg->vector().begin(),
                     new_arg->vector().end(), profiling);
>>>>>>> 7cb4e1620... Fixes for cldrive.:gpu/cldrive/array_kernel_arg_value.h
    return std::move(new_arg);
  }

 private:
  cl::Buffer buffer_;
};

}  // namespace cldrive
}  // namespace gpu
