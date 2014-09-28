#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from ..utils import decimal_string, parse_gerber_value, write_gerber_value


def test_zero_suppression():
    """ Test gerber value parser and writer handle zero suppression correctly.
    """
    # Default format
    format = (2, 5)
    
    # Test leading zero suppression
    zero_suppression = 'leading'
    test_cases = [('1', 0.00001), ('10', 0.0001), ('100', 0.001),
        ('1000', 0.01), ('10000', 0.1), ('100000', 1.0),('1000000', 10.0),
        ('-1', -0.00001), ('-10', -0.0001), ('-100', -0.001),
        ('-1000', -0.01), ('-10000', -0.1), ('-100000', -1.0),('-1000000', -10.0),]
    for string, value in test_cases:
        assert(value == parse_gerber_value(string,format,zero_suppression))
        assert(string == write_gerber_value(value,format,zero_suppression))
    
    # Test trailing zero suppression
    zero_suppression = 'trailing'
    test_cases = [('1', 10.0), ('01', 1.0), ('001', 0.1), ('0001', 0.01),
        ('00001', 0.001), ('000001', 0.0001), ('0000001', 0.00001),
        ('-1', -10.0), ('-01', -1.0), ('-001', -0.1), ('-0001', -0.01),
        ('-00001', -0.001), ('-000001', -0.0001), ('-0000001', -0.00001)]
    for string, value in test_cases:
        assert(value == parse_gerber_value(string,format,zero_suppression))
        assert(string == write_gerber_value(value,format,zero_suppression))



def test_format():
    """ Test gerber value parser and writer handle format correctly
    """
    zero_suppression = 'leading'
    test_cases = [((2,7),'1',0.0000001), ((2,6),'1',0.000001),
        ((2,5),'1',0.00001), ((2,4),'1',0.0001), ((2,3),'1',0.001),
        ((2,2),'1',0.01), ((2,1),'1',0.1), ((2,7),'-1',-0.0000001),
        ((2,6),'-1',-0.000001), ((2,5),'-1',-0.00001), ((2,4),'-1',-0.0001),
        ((2,3),'-1',-0.001), ((2,2),'-1',-0.01), ((2,1),'-1',-0.1),]
    for format, string, value in test_cases:
        assert(value == parse_gerber_value(string,format,zero_suppression))
        assert(string == write_gerber_value(value,format,zero_suppression))
        
    zero_suppression = 'trailing'
    test_cases = [((6, 5), '1' , 100000.0), ((5, 5), '1', 10000.0),
        ((4, 5), '1', 1000.0), ((3, 5), '1', 100.0),((2, 5), '1', 10.0),
        ((1, 5), '1', 1.0), ((6, 5), '-1' , -100000.0),
        ((5, 5), '-1', -10000.0), ((4, 5), '-1', -1000.0),
        ((3, 5), '-1', -100.0),((2, 5), '-1', -10.0), ((1, 5), '-1', -1.0),]
    for format, string, value in test_cases:
        assert(value == parse_gerber_value(string,format,zero_suppression))
        assert(string == write_gerber_value(value,format,zero_suppression))


def test_decimal_truncation():
    """ Test decimal string truncates value to the correct precision
    """
    value = 1.123456789
    for x in range(10):
        result = decimal_string(value, precision=x)
        calculated = '1.' + ''.join(str(y) for y in range(1,x+1))
        assert(result == calculated)