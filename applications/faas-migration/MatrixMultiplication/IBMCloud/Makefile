build: clean
	dotnet restore
	dotnet publish -c Release -o out
	cd out/ && zip -r -0 matrix-mul.zip *

deploy_actions: build
	cd out && ibmcloud fn action create create-matrix matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.CreateMatrix::Main --kind dotnet:2.2 -P ../s3_credentials.json -a final true
	cd out && ibmcloud fn action create serial-multiply matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.SerialMultiply::Main --kind dotnet:2.2
	cd out && ibmcloud fn action create distribute-work matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.DistributeWork::Main --kind dotnet:2.2  
	cd out && ibmcloud fn action create parallel-worker matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.ParallelWorker::Main --kind dotnet:2.2
	cd out && ibmcloud fn action create build-result matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.BuildResult::Main --kind dotnet:2.2
	cd out && ibmcloud fn action create generate-report matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.GenerateReport::Main --kind dotnet:2.2

update_actions: build
	cd out && ibmcloud fn action update create-matrix matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.CreateMatrix::Main --kind dotnet:2.2 -P ../s3_credentials.json -a final true 
	cd out && ibmcloud fn action update serial-multiply matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.SerialMultiply::Main --kind dotnet:2.2
	cd out && ibmcloud fn action update distribute-work matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.DistributeWork::Main --kind dotnet:2.2  
	cd out && ibmcloud fn action update parallel-worker matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.ParallelWorker::Main --kind dotnet:2.2
	cd out && ibmcloud fn action update build-result matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.BuildResult::Main --kind dotnet:2.2
	cd out && ibmcloud fn action update generate-report matrix-mul.zip --main MatrixMul::MatrixMul.IBMCloud.GenerateReport::Main --kind dotnet:2.2

deploy_workflow:
	compose workflow.js > out/workflow.json
	deploy workflow out/workflow.json -w

deploy: deploy_actions deploy_workflow

update: update_actions deploy_workflow

invoke:
	ibmcloud fn action invoke workflow -r -P redis_credentials.json

destroy_actions:
	ibmcloud fn action delete create-matrix
	ibmcloud fn action delete serial-multiply
	ibmcloud fn action delete distribute-work
	ibmcloud fn action delete build-result
	ibmcloud fn action delete generate-report
	ibmcloud fn action delete workflow
	ibmcloud fn action delete choose-type
	ibmcloud fn action delete set-worker-count
	ibmcloud fn action delete set-worker-id-0
	ibmcloud fn action delete set-worker-id-1
	ibmcloud fn action delete set-worker-id-2
	ibmcloud fn action delete set-worker-id-3
	ibmcloud fn action delete set-worker-id-4
	ibmcloud fn action delete cleanup-context
	ibmcloud fn action delete zero-out-worker-count

clean:
	rm -rvf bin/
	rm -rvf out/
