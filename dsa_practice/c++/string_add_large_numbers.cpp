#include <bits/stdc++.h> 
string stringSum(string &num1, string &num2) {
	long x = 0, y = 0;
	unsigned short int a = 0, b = 0, carry = 0;
	string res;
	x = num1.size() - 1;
	y = num2.size() - 1;
	while(x >= 0 && y >= 0){
		a = num1.at(x) - '0';
		b = num2.at(y) - '0';

		a += b + carry;
		b = a % 10;
		carry = a/10;

		res.push_back('0' + b);
		--x;
		y--;
	}
	while(x >= 0){
		a = num1.at(x) - '0';
		a += carry;
		res.push_back('0' + (a%10));
		carry = a / 10;
		x--;
	}
	while(y >= 0){
		b = num2.at(y) - '0';
		b += carry;
		res.push_back('0' + (b%10));
		carry = b / 10;
		--y;
	}
	if(carry>0) res.push_back('0' + carry);
	reverse(res.begin(), res.end());
	return res;
}
