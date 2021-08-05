PROJECT_NAME="scheduler_deployment"

rm -rf $PROJECT_NAME

mkdir $PROJECT_NAME
mkdir $PROJECT_NAME/var/
mkdir $PROJECT_NAME/var/task

cp Dockerfile $PROJECT_NAME/Dockerfile
cp requirements.txt $PROJECT_NAME/requirements.txt

cp ../scheduler_model.py $PROJECT_NAME/var/task/scheduler_model.py 
cp ../test_scheduler.py $PROJECT_NAME/var/task/test_scheduler.py 
cp ./api.py $PROJECT_NAME/var/task/api.py 
#cp ./handler.py lambda_deployment/var/task/handler.py 

cd $PROJECT_NAME 
sudo docker build -t $PROJECT_NAME .