# vcgencmd display_power 0   # 关闭 HDMI
# vcgencmd display_power 1   # 开启 HDMI



cd /home/xuanpeichen
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


cd /home/xuanpeichen

wget https://github.com/WiringPi/WiringPi/releases/download/2.61-1/wiringpi-2.61-1-arm64.deb
sudo dpkg -i wiringpi-2.61-1-arm64.deb
gpio -v
rm -rf wiringpi-2.61-1-arm64.deb


cd /home/xuanpeichen

python3 -m venv myenv
source ~/myenv/bin/activate


# deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm main contrib non-free
# deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main contrib non-free
# deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free
sudo apt-get update
sudo apt-get install -y libgtk-4-1 libgraphene-1.0-0

cd /home/xuanpeichen/Desktop/Ink-wash-photo-frame

pip3 install -r requirement.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple
playwright install


sudo raspi-config nonint do_spi 0


sudo systemctl daemon-reload
sudo systemctl enable startscript.service
sudo systemctl start startscript.service

chmod +x /home/xuanpeichen/Desktop/Ink-wash-photo-frame/start.sh

# pip3 install RPi.GPIO -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip3 install pillow numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip3 install spidev -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip3 install gpiozero -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip3 install lgpio -i https://pypi.tuna.tsinghua.edu.cn/simple
