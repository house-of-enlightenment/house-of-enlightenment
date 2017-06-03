gulp prod
ssh oceanstar 'mkdir -p ~/www/house-of-enlightenment'
scp -r ./build/* oceanstar:~/www/house-of-enlightenment
