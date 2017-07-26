gulp simulator-build --env production
ssh oceanstar 'mkdir -p ~/www/house-of-enlightenment'
scp -r ./build/* oceanstar:~/www/house-of-enlightenment
scp -r ./server/* oceanstar:~/www/house-of-enlightenment
# HACK
scp ../../layout/hoeLayout.json oceanstar:~/www/house-of-enlightenment/layout.json
