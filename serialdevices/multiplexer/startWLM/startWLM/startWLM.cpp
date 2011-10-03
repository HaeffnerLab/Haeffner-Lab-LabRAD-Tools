#include "stdafx.h"
#include <iostream>
#include "wlmData.h"
using namespace std;

int startWLM(){
	cout << "Starting WLM" << endl;
	int ret = ControlWLM(cCtrlWLMShow,0,0);
	cout << ret << endl;
	return ret;
}

int _tmain(int argc, _TCHAR* argv[])
{
	startWLM();
	return 0;
}
