#include <bits/stdc++.h> 
string convertString(string str) 
{
	long i = 1;
	if(str[0] >= 97 && str[0] <= 122) str[0] -= 32;
	while(str[i] != '\0'){
		if((str[i-1] == 32) && (str[i] >= 97) && (str[i] <= 122)) str[i] -= 32; // or
    // if((str[i-1] == ' ') && (str[i] >= 'a') && (str[i] <= 'z')) str[i] -= 32;
    // this is slower because (>,<) comparison requires character to be converted to ASCII integer first
		++i;
	}
	return str;
}
