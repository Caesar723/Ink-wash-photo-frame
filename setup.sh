# vcgencmd display_power 0   # 关闭 HDMI
# vcgencmd display_power 1   # 开启 HDMI




wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.60.tar.gz
tar zxvf bcm2835-1.60.tar.gz 
cd bcm2835-1.60/
sudo ./configure
sudo make
sudo make check
sudo make install

rm -rf bcm2835-1.60.tar.gz

git config --global user.name "Caesar723"
git config --global user.email "13122531903@163.com"


wget https://github.com/WiringPi/WiringPi/releases/download/2.61-1/wiringpi-2.61-1-arm64.deb
sudo dpkg -i wiringpi-2.61-1-arm64.deb
gpio -v
rm -rf wiringpi-2.61-1-arm64.deb


python3 -m venv myenv
source ~/myenv/bin/activate

pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple
playwright install

# pip3 install RPi.GPIO -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip3 install pillow numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip3 install spidev -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip3 install gpiozero -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip3 install lgpio -i https://pypi.tuna.tsinghua.edu.cn/simple
