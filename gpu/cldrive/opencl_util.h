#pragma once

#include "gpu/cldrive/profiling_data.h"
#include "third_party/opencl/include/cl.hpp"

namespace gpu {
namespace cldrive {

// Blocking host to device copy operation between iterators and a buffer.
// Returns the elapsed nanoseconds.
template <typename IteratorType>
void CopyHostToDevice(const cl::CommandQueue &queue, IteratorType startIterator,
                      IteratorType endIterator, const cl::Buffer &buffer,
                      ProfilingData *profiling) {
  typedef typename std::iterator_traits<IteratorType>::value_type ValueType;
  size_t length = endIterator - startIterator;
  size_t byteLength = length * sizeof(ValueType);

  cl::Event event;
  ValueType *pointer = static_cast<ValueType *>(queue.enqueueMapBuffer(
      buffer, /*blocking=*/true, /*flags=*/CL_MAP_WRITE, /*offset=*/0,
      /*size=*/byteLength, /*events=*/nullptr, /*event=*/&event,
      /*error=*/nullptr));
  profiling->elapsed_nanoseconds += GetElapsedNanoseconds(event);
  std::copy(startIterator, endIterator, pointer);

  queue.enqueueUnmapMemObject(buffer, pointer, /*events=*/nullptr, &event);

  // Set profiling data.
  profiling->elapsed_nanoseconds += GetElapsedNanoseconds(event);
  profiling->transferred_bytes += byteLength;
}

// Blocking host to device copy operation between iterators and a buffer.
// Returns the elapsed nanoseconds.
template <typename IteratorType>
void CopyDeviceToHost(const cl::CommandQueue &queue, const cl::Buffer &buffer,
                      IteratorType startIterator,
                      const IteratorType endIterator,
                      ProfilingData *profiling) {
  typedef typename std::iterator_traits<IteratorType>::value_type ValueType;
  size_t length = endIterator - startIterator;
  size_t byteLength = length * sizeof(ValueType);

  cl::Event event;
  ValueType *pointer = static_cast<ValueType *>(queue.enqueueMapBuffer(
      buffer, /*blocking=*/true, /*flags=*/CL_MAP_READ, /*offset=*/0,
      /*size=*/byteLength, /*events=*/nullptr, /*event=*/&event,
      /*error=*/nullptr));
  profiling->elapsed_nanoseconds += GetElapsedNanoseconds(event);
  std::copy(pointer, pointer + length, startIterator);

  queue.enqueueUnmapMemObject(buffer, pointer, /*events=*/nullptr, &event);

  // Set profiling data.
  profiling->elapsed_nanoseconds += GetElapsedNanoseconds(event);
  profiling->transferred_bytes += byteLength;
}

}  // namespace cldrive
}  // namespace gpu
