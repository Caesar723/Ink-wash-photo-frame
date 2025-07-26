


wget https://github.com/WiringPi/WiringPi/releases/download/2.61-1/wiringpi-2.61-1-arm64.deb

sudo dpkg -i wiringpi-2.61-1-arm64.deb



python3 -m venv myenv

pip3 install RPi.GPIO

pip3 install pillow numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

pip3 install spidev -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install gpiozero -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install lgpio -i https://pypi.tuna.tsinghua.edu.cn/simple
