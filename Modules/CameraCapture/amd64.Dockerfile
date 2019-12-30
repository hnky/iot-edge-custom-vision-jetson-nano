FROM python:3.7-slim

RUN echo "BUILD MODULE: CameraCapture"

RUN apt-get update \
    && apt-get install -y \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
        yasm \
        pkg-config \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavformat-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install numpy

ENV OPENCV_VERSION="4.1.1"
RUN wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip \
&& unzip ${OPENCV_VERSION}.zip \
&& mkdir /opencv-${OPENCV_VERSION}/cmake_binary \
&& cd /opencv-${OPENCV_VERSION}/cmake_binary \
&& cmake -DBUILD_TIFF=ON \
  -DBUILD_opencv_java=OFF \
  -DWITH_CUDA=OFF \
  -DWITH_OPENGL=ON \
  -DWITH_OPENCL=ON \
  -DWITH_IPP=ON \
  -DWITH_TBB=ON \
  -DWITH_EIGEN=ON \
  -DWITH_V4L=ON \
  -DBUILD_TESTS=OFF \
  -DBUILD_PERF_TESTS=OFF \
  -DCMAKE_BUILD_TYPE=RELEASE \
  -DCMAKE_INSTALL_PREFIX=$(python3.7 -c "import sys; print(sys.prefix)") \
  -DPYTHON_EXECUTABLE=$(which python3.7) \
  -DPYTHON_INCLUDE_DIR=$(python3.7 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
  -DPYTHON_PACKAGES_PATH=$(python3.7 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
  .. \
&& make install \
&& rm /${OPENCV_VERSION}.zip \
&& rm -r /opencv-${OPENCV_VERSION}

RUN ln -s \
  /usr/local/python/cv2/python-3.7/cv2.cpython-37m-x86_64-linux-gnu.so \
  /usr/local/lib/python3.7/site-packages/cv2.so


RUN pip install requests tornado==4.5.3
RUN pip install azure-iot-device
#trollius

#RUN apt-get install libboost-python-dev
#RUN pip install azure-iothub-device-client




WORKDIR /app



# Install Python packages
#COPY /build/amd64-requirements.txt ./
#RUN pip3 install --upgrade pip
#RUN pip3 install --upgrade setuptools

#RUN pip3 install -U --pre janus==0.4.0
#RUN pip3 install -U azure-iot-device
#RUN pip3 install -r amd64-requirements.txt

#RUN pip3 install -U numpy==1.17

#RUN apt-get install -y python-opencv

#RUN pip3 install opencv3-python

# Cleanup
#RUN rm -rf /var/lib/apt/lists/* \
#    && apt-get -y autoremove

ADD /app/ .

# Expose the port
EXPOSE 5012

#CMD python main.py

ENTRYPOINT [ "python", "-u", "./main.py" ]

