# MUSICC - Multi User Scenario Catalogue for Connected and Autonomous Vehicles
# Copyright (C)2020 Connected Places Catapult
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: musicc-support@cp.catapult.org.uk
#          https://cp.catapult.org.uk/case-studies/musicc/'
#
## @package queries
#  This module contains classes for the interpretation and evaluation of query strings into Django Q objects
import re
from django.db.models import Q
from musicc.models.MusiccScenario import MusiccScenario

## The QueryParser class contains function for parsing logical comparisons and boolean expressions<br>
#  It allows conversion of expressions to postfix format and custom processing of operators<br>
#  This includes modifying order of operations, adding operators and mapping them to different functions
class QueryParser:
    ## A dictionary of all operators including their precedence, number of operands and a function for how to execute
    operators = {
        "=": {
            "precedence": 0,
            "operands": 2,
            "operation": lambda operands: Q(
                **{"metadata__" + operands[0] + "__iexact": operands[1]}
            ),
        },
        "==": {
            "precedence": 0,
            "operands": 2,
            "operation": lambda operands: Q(
                **{"metadata__" + operands[0] + "__iexact": operands[1]}
            ),
        },
        ">": {
            "precedence": 0,
            "operands": 2,
            "operation": lambda operands: Q(
                **{"metadata__" + operands[0] + "__gt": infer_data_type(operands[1])}
            ),
        },
        "<": {
            "precedence": 0,
            "operands": 2,
            "operation": lambda operands: Q(
                **{"metadata__" + operands[0] + "__lt": infer_data_type(operands[1])}
            ),
        },
        "<=": {
            "precedence": 0,
            "operands": 2,
            "operation": lambda operands: Q(
                **{"metadata__" + operands[0] + "__lte": infer_data_type(operands[1])}
            ),
        },
        ">=": {
            "precedence": 0,
            "operands": 2,
            "operation": lambda operands: Q(
                **{"metadata__" + operands[0] + "__gte": infer_data_type(operands[1])}
            ),
        },
        "!=": {
            "precedence": 0,
            "operands": 2,
            "operation": lambda operands: ~Q(
                **{"metadata__" + operands[0] + "__iexact": operands[1]}
            ),
        },
        "CONTAINS": {
            "precedence": 0,
            "operands": 2,
            "operation": lambda operands: Q(
                **{"metadata__" + operands[0] + "__icontains": operands[1]}
            ),
        },
        "INCLUDES": {
            "precedence": 0,
            "operands": 2,
            "operation": lambda operands: Q(
                **{"metadata__" + operands[0] + "__contains": [operands[1]]}
            ),
        },
        "AND": {
            "precedence": 2,
            "operands": 2,
            "operation": lambda operands: operands[0] & operands[1],
        },
        "OR": {
            "precedence": 3,
            "operands": 2,
            "operation": lambda operands: operands[0] | operands[1],
        },
        "NOT": {
            "precedence": 1,
            "operands": 1,
            "operation": lambda operands: ~Q(operands[0]),
        },
        "(": {},
        ")": {},
    }

    special_evaluations = {
        # If the user is seaching tags, search both user tags and global tags
        "Tags__Tag": lambda self, operand: (
            Q(
                **{
                    "label__in": [
                        m.label
                        for m in MusiccScenario.active_objects.filter(
                            Q(
                                **{
                                    "tag__name__iexact": operand,
                                    "tag__active": True,
                                    "tag__updated_by_user": self.user,
                                    "revision": self.revision
                                }
                            )
                        )
                    ]
                }
            )
        )
        | Q(**{"metadata__GlobalTags__GlobalTag__contains": [operand]}),
        "MUSICC_ID": lambda self, operand: (
            MusiccScenario.query_from_human_readable_id(operand)
        ),
        "OpenScenario_ID": lambda self, operand: (
            MusiccScenario.query_osc_from_human_readable_id(operand)
        ),
        "OpenDrive_ID": lambda self, operand: (
            MusiccScenario.query_odr_from_human_readable_id(operand)
        )
    }

    ## A regex for identifying individaul tokens in an expression including operators, string, numbers and other types
    regex = r"[=<>()!][=]{0,1}|[\"][^\"]*[\"]|['][^']*[']|[\S.]+"

    ## The constructor
    #  @param expression The expression which this object will evaluate
    def __init__(self, expression):
        self.expression = expression

    ## Returns true if the given token is NOT in the list of operators
    #  @param token A token string
    #  @return A boolean representing if the token is NOT an operator
    def _is_operand(self, token):
        return not self._is_operator(token)

    ## Returns true if the given token is in the list of operators
    #  @param token A token string
    #  @return A boolean representing if the token is an operator
    def _is_operator(self, token):
        return isinstance(token, str) and token.upper() in self.operators

    ## Returns true if the given operator has an operand value of 1 in the operator dictionary
    #  @param operator An operator
    #  @return A boolean representing if the operator takes one operand
    def _is_unary_operator(self, operator):
        return self.operators[operator]["operands"] == 1

    ## Returns the last element of a list without removing it
    #  @param stack The list to peek
    #  @return The last element in the list if the list is not empty, otherwise None
    def _peek(self, stack):
        return stack[-1] if stack else None

    ## Add a postfix string representation of an operation to the values array
    #  If it's a binary operator the value added will be of the form:<br>
    #  "[operator] [operand1] [operand2]"
    #  If it's a unary operator the value added will be of the form:<br>
    #  "[operator] [operand1]"
    #  @param operators The list of operators
    #  @param values The list of values
    def _apply_operator(self, operators, values):
        operator = operators.pop()
        right = values.pop()
        if not self._is_unary_operator(operator):
            left = values.pop()
            values.append("{0} {1} {2} ".format(operator, left, right))
        else:
            values.append("{0} {1} ".format(operator, right))

    ## Tests if one operator has a greater precedence than another
    #  @param op1 The first operator
    #  @param op2 The second operator
    #  @return Return true if the first operator has a greater precedence than the second
    def _greater_precedence(self, op1, op2):
        return self.operators[op1]["precedence"] < self.operators[op2]["precedence"]

    ## Uses the shunting yard algorithm to convert an expression to postfix<br>
    #  @param expression The string expression to be converted
    #  @return The string expression in postfix notation
    def _convert_to_postfix(self, expression):
        tokens = re.findall(self.regex, expression)
        values = []
        operators = []
        for token in tokens:
            if self._is_operand(token):
                values.append(token)
            elif token == "(":
                operators.append(token)
            elif token == ")":
                top = self._peek(operators)
                while top is not None and top != "(":
                    self._apply_operator(operators, values)
                    top = self._peek(operators)
                operators.pop()  # Discard the '('
            else:
                # Operator
                token = token.upper()
                top = self._peek(operators)
                while (
                    top is not None
                    and top not in "()"
                    and self._greater_precedence(top, token)
                ):
                    self._apply_operator(operators, values)
                    top = self._peek(operators)
                operators.append(token)
        while self._peek(operators) is not None:
            self._apply_operator(operators, values)
        return values[0]

    ## Iterates over a postfix expression in order to parse and execute operations
    #  @param postfix_expression The postfix expression
    #  @return The parsed Q object result of the expression
    def _evaluate_postfix(self, postfix_expression):
        start_tokens = re.findall(self.regex, postfix_expression)
        while len(start_tokens) > 1:
            operator = ""
            operands = []
            new_tokens = []
            for token in start_tokens:
                if self._is_operand(token):
                    if (
                        isinstance(token, str)
                        and re.match(r"['\"]", token[0])
                        and re.match(r"['\"]", token[-1])
                    ):
                        token = token.strip('"').strip("'")
                    operands.append(token)
                else:
                    self._append_if_not_empty(new_tokens, operator)
                    new_tokens.extend(operands)
                    operator = token
                    operands = []

                if (
                    operator != ""
                    and len(operands) == self.operators[operator]["operands"]
                ):
                    result_of_operation = self._evaluate_operation(operator, operands)
                    new_tokens.append(result_of_operation)
                    operator = ""
                    operands = []

            self._append_if_not_empty(new_tokens, operator)
            new_tokens.extend(operands)

            start_tokens = new_tokens
        return start_tokens[0]

    ## Add a string element to a list if the element is not empty
    #  @param list The target list
    #  @param element The string element to be appended
    def _append_if_not_empty(self, list, element):
        if element != None and element != "":
            list.append(element)

    ## Execute an operator's operation with the given operands
    #  @param operator The string operator to execute
    #  @param operands an array holding the poerands to be executed on
    #  @return The result of the operation
    def _evaluate_operation(self, operator, operands):
        if self._is_operator(operator):
            if operands[0] in self.special_evaluations:
                return self.special_evaluations[operands[0]](self, operands[1])
            else:
                return self.operators[operator]["operation"](operands)

    ## Evaluate this object's expression
    def evaluate(self, user, revision=None):
        self.user = user
        self.revision = revision
        if not self.expression or self.expression == "*":
            return Q()
        return self._evaluate_postfix(self._convert_to_postfix(self.expression))


## Attempt to infer the type of a string and return it in the inferred type
#  Currently supports ints and floats
#  @param string The string representation of the value
#  @return The parsed value or the original string
def infer_data_type(string):
    try:
        return int(string)
    except:
        pass

    try:
        return float(string)
    except:
        pass

    return string
