#include "stdafx.h"
#include <iostream>
#include "wlmData.h"
#include <cstdlib> 
using namespace std;

void setExp(int x){
	SetExposure(x);
}

int _tmain(int argc, char* argv[]){	
	int exp;
	cin >> exp;
	setExp(exp);
	return 0;
}

