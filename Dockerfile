FROM alpine:latest

# Install build dependencies and tools for static compilation
RUN apk add --no-cache \
    build-base \
    musl-dev \
    gcc \
    g++ \
    make \
    cmake \
    autoconf \
    automake \
    bison \
    flex \
    libtool \
    pkgconfig \
    git \
    curl \
    wget \
    tar \
    gzip \
    bzip2 \
    xz \
    patch \
    ca-certificates \
    perl \
    file \
    linux-headers \
    libevent-dev

# Set environment variables for static compilation
ENV CFLAGS="-static -Os -fPIC" \
    CXXFLAGS="-static -Os -fPIC" \
    LDFLAGS="-static" \
    CC="gcc" \
    CXX="g++" \
    PKG_CONFIG="pkg-config --static"

# Create directories for building
RUN mkdir -p /build /src /output

# Set working directory
WORKDIR /build

# Default command
CMD ["/bin/sh"]
