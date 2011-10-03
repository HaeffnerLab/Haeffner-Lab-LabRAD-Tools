#include "stdafx.h"
#include <iostream>
#include "wlmData.h"
using namespace std;

int startMeasurement(){
	Operation(cCtrlStartMeasurement);
	int ret = GetOperationState(0);
	return ret;
}

int _tmain(int argc, _TCHAR* argv[])
{
	startMeasurement();
	return 0;
}

