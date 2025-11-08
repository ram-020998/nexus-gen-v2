# Enhanced Appian SAIL Expression Grammar
#
# This grammar is intended for use in GENERATING Appian SAIL expressions.
# SAIL runs within an Appian "low-code" environment which provides things like user sessions, a document management system, user preferred calendars, data records, web access, system health checks, etc.
# These expressions may be used for snippets of functionality, defining reusable rules based on expressions, full user interfaces, etc.
#
# Keyword and positional parameter meanings are expressed solely through comments.
# Tables and lists of valid values are given in comments.
# The root element for parsing and generating SAIL expressions is root.
#
# SAIL's type system supports 32-bit integers, 64-bit double floating-point (often called decimal), strings, booleans, maps, dictionaries (same as maps, but all values wrapped in a Variant (Any Type)), arrays, and CDTs (Complex DataTypes).
#
# ALL SAIL functions are side-effect free, just returning their result to be acted upon by the caller.
# CRITICAL RULE: ONLY the functions specified in this grammar exist. Do not use other functions.

# COMMON MISTAKES TO AVOID:

# 1. Logical operators (use functions, not operators)
# WRONG: if(a and b, ...)     RIGHT: if(and(a, b), ...)
# WRONG: if(a or b, ...)      RIGHT: if(or(a, b), ...)

# 2. Local variable reuse in same block
# WRONG: a!localVariables(local!x: 1, local!x: 2)
# RIGHT: a!localVariables(local!x: 1, local!y: 2)

# 3. save!value usage outside a!save
# WRONG: if(save!value, a!save(...), {})
# RIGHT: a!save(value: if(save!value, newVal, oldVal))

root ::= expression

# Top-level expression
expression ::= assignment_expression | comparison_expression | concatenation_expression

# Assignment expressions
#
# Each local_variable defined in the same a!localVariables block must be uniquely named.
# Local variables are scoped to be visible in subsequently defined variables and in a!localVariable's final expression
assignment_expression ::= "a!localVariables" "(" local_variable_list "," expression ")"
# CRITICAL RULE: Within the same a!localVariables block, each local variable MUST have a unique name
# WRONG: a!localVariables(local!x: 1, local!x: local!x + 1, local!x)
# RIGHT: a!localVariables(local!x: 1, local!y: local!x + 1, local!y)
# Each local variable is visible to subsequently defined variables in the same block
local_variable_list ::= local_variable ("," local_variable)*
local_variable ::= "local!" identifier ":" expression

# Comparison expressions (lowest precedence)
# When comparing text, = does case insensitive comparison; use isnull for null checking instead of =
# IMPORTANT: SAIL does not support and/or as infix operators
# Use function syntax: and(condition1, condition2, ...) and or(condition1, condition2, ...)
# NOT: condition1 and condition2
# IMPORTANT: Comparisons should be made only between the same type, do not count on automatic casting.
comparison_expression ::= concatenation_expression (comparison_operator concatenation_expression)*
comparison_operator ::= "=" | "<>" | "<" | ">" | "<=" | ">="
# NOTE: and/or are FUNCTIONS only, not operators - use and(a,b) not a and b

# String concatenation (highest precedence after parentheses)
concatenation_expression ::= additive_expression ("&" additive_expression)*

# Arithmetic expressions
# Can act on numbers and number arrays, e.g., 2+3 returns 5, {1,10}+3 returns {4,13}, {1,10}+{3,5} returns {4,15}
# + does not act as string concatenation, only addition; strings are cast to numbers first, so "123"+"4" returns 127
additive_expression ::= multiplicative_expression (additive_operator multiplicative_expression)*
additive_operator ::= "+" | "-"

# Can act on numbers and number arrays, e.g., 2*3 returns 6, {1,10}*3 returns {3,30}, {1,10}*{3,5} returns {3,50}
# division by scalar 0 yields an exception "Denominator may not be zero (0)"
# division by an array of numbers containing 0 yields an infinity for 0 denominators, e.g., {1.0,2.0,3.0}/{4.0,0.0,5.0} yields {0.25, infinity(), 0.6} to allow filtering
multiplicative_expression ::= exponential_expression (multiplicative_operator exponential_expression)*
multiplicative_operator ::= "*" | "/"

# Can act on numbers and number arrays, e.g., 2^3 returns 8, {1,10}^3 returns {1,1000}, {1,10}^{3,5} returns {1,100000}
exponential_expression ::= unary_expression ("^" unary_expression)*

unary_expression ::= "-" unary_expression | percentage_expression

# % divides a number by 100, e.g., 25% is the same as .25; it does NOT act as a modulo operator (use mod function for that)
percentage_expression ::= primary_expression "%" | primary_expression

# Primary expressions
primary_expression ::= literal
                    | variable
                    | function_call
                    | type_constructor
                    | array
                    | map
                    | dictionary
                    | index_access
                    | field_access
                    | "(" expression ")"

# Literals
literal ::= string_literal | number_literal | boolean_literal | null_literal

string_literal ::= quoted_string | multiline_string
# Note that double-quote characters are escaped in quoted_string literals by doubling the double-quote character, not using backslash, e.g., "He said, ""Hello""."
quoted_string ::= '"' string_char* '"'
string_char ::= [^"] | '""'
multiline_string ::= "***" [^*]* "***"

number_literal ::= integer_literal | double_literal | bigrational_literal

integer_literal ::= "-"? digit+
double_literal ::= "-"? (digit+ "." digit* | "." digit+ | digit+ ".") ([eE] "-"? digit+)?

boolean_literal ::= "true" | "false"
null_literal ::= "null"

# Variables
variable ::= domain_variable | simple_identifier
domain_variable ::= domain "!" identifier
domain ::= "pm" | "pv" | "pp" | "tp" | "ac" | "msg" | "cons" | "ri" | "bind" | "parse" | "local"
        | "rf" | "rp" | "rt" | "rv" | "rip" | "recordType" | "rsp" | "rvp" | "flow" | "sasa" | "save" | "env"
        | "test" | "sdx" | "syn" | "http" | "fv" | "data" | "fn" | "rule" | "a" | "ext" | "int" | "type"
        | "custom" | "chain" | "chart" | "ts" | "portal"

# Identifiers
identifier ::= simple_identifier | complex_identifier
simple_identifier ::= identifier_start identifier_char*
complex_identifier ::= "'" [^']+ "'"
identifier_start ::= [a-zA-Zλ]
identifier_char ::= [a-zA-Zλ0-9_]

# Function calls with comprehensive function names
function_call ::= function_name "(" argument_list? ")"
function_name ::= sail_function | domain "!" identifier | identifier

# Complete list of SAIL functions organized by parameter type
sail_function ::= array_function_positional | array_function_keyword
                | arrayset_function_positional
                | base_conversion_function_positional
                | connector_function_keyword
                | conversion_function_positional
                | serialization_function_positional
                | custom_fields_function_keyword
                | data_builder_function_positional | data_builder_function_keyword
                | date_time_function_positional | date_time_function_keyword
                | evaluation_function_keyword | evaluation_function_mixed
                | informational_function_positional | informational_function_keyword
                | interface_component_function_keyword
                | logical_function_positional | logical_function_mixed
                | predicate_looping_function_positional | looping_function_positional | looping_function_mixed
                | mathematical_function_positional | mathematical_function_keyword
                | people_function_positional | people_function_keyword
                | scripting_function_positional | scripting_function_keyword | scripting_function_mixed
                | smart_service_function_keyword
                | statistical_function_positional
                | system_function_positional | system_function_keyword | system_function_mixed
                | text_function_positional | text_function_keyword | text_function_mixed
                | trigonometry_function_positional

# Array functions
# merge({1, 2, 3}, {4, 5, 6}) would return {{1, 4}, {2, 5}, {3, 6}}
# merge({1, 2, 3}, {4, 5}) would return {{1, 4}, {2, 5}, {3, null}}
# As always in SAIL, none of these mutate the passed data.
array_function_positional ::= "a!flatten" ; array (Any Type Array); converts given array that contains other arrays into an array of single items; returns an array
                            | "append" ; array (Any Type array), value (Any Type); appends a value or values to the given array, and returns the resulting array, e.g., append({10,20},{30,40}) returns {10,20,30,40}, append({10,20},30) returns {10,20,30}
                            | "index" ; array (Any Type), index (Integer, 1-based), default (Any Type, optional); returns the data[index] if it is valid or else returns the default value, e.g., index({10, 20, 30}, 2, 1) returns 20
                            | "insert" ; array (Any Type), value (Any Type), index (Number, 1-based); inserts a value into the given array and returns the resulting array, e.g., insert({10, 20, 30, 40}, 100, 1) returns {100, 10, 20, 30, 40}
                            | "joinarray" ; array (Any Type Array), separator (Text, optional); concatenates the elements of an array together into one string and inserts a string separator between each element, e.g., joinarray({1, 2, 3, 4}, "|") returns "1|2|3|4"
                            | "ldrop" ; array (Any Type), number (Number); drops a given number of values from the left side of an array and returns the resulting array, e.g., ldrop({10, 20, 30, 40, 50}, 2) returns {30, 40, 50}
                            | "length" ; array (Any Type); return the length of the array, e.g., length({10, "alpha", 17, "beta", 3}) returns 5
                            | "rdrop" ; array (Any Type), number (Number); drops a given number of values from the right side of an array, and returns the resulting array, e.g., rdrop({10, 20, 30, 40, 50}, 2) returns {10, 20, 30}
                            | "remove" ; array (Any Type), index (Number or Number array, 1-based); removes the value at a given index from an array, and returns the resulting array, e.g., remove({10, 20, 30, 40}, {2, 4}) returns {10, 30}
                            | "reverse" ; array (Any Type); returns an array in reverse order, e.g., reverse({10, 20, 30, 40}) returns {40, 30, 20, 10}
                            | "updatearray" ; array (Any Type), index (Number, 1-based), value (Any Type); modifies existing values at the specified index of a given array, and returns the resulting array, e.g., updatearray({1, 2, 3}, 2, 200) returns {1,200,3}
                            | "where" ; booleanArray (Boolean Array); returns the 1-based indexes where the values in the input array are true (useful for filtering by index), e.g., a!localVariables(local!data:{2,10,1,3,8,0,-2,100,5}, local!indices:where(local!data>3), local!data[local!indices]) returns {10,8,100,5}
                            | "wherecontains" ; valuesToFind (Any Type array), arrayToFindWithin (Any Type array); returns array of indexes that indicate the position of the valuesToFind within the arrayToFindWithin, e.g., wherecontains(20, {10, 20, 30}) returns {2}, wherecontains(50, {10, 20, 30}) returns {}, wherecontains({2, 1}, {1, 2, 5, 2, 3}) returns {1, 2, 4}
                            | "merge" ; array ... (variadic Any Type Array parameters); Takes a variable number of lists and merges them into a single list (or a list of lists) that is the size of the largest list provided.

arrayset_function_positional ::= "contains" ; arrayToFindWithin (Any Type), valueToFind (must be element of arrayToFindWithin's type); e.g., contains({"A", "b", "c"}, "A") returns true, contains({"A", "b", "c"}, "a") returns false, contains({1, 2, 3}, 2) returns true, contains({1, 2.2, 3.3}, todecimal(1)) returns true, contains({1, 2, 3}, {1, 2}) returns true, contains({1, 2, 3}, {1, 4}) returns false
                               | "difference" ; array1 (Any Type), array2 (Any Type); returns the values in array1 and not in array2, e.g., difference({1, 2, 3, 4}, {3, 4}) returns {1, 2}
                               | "intersection" ; array1 (Any Type), array2 (Any Type); returns only those elements that appear in all of the given arrays, e.g., intersection({1, 2, 3, 4}, {3, 4, 5, 6}) returns {3, 4}
                               | "symmetricdifference" ; array1 (Any Type), array2 (Any Type); returns the values from two integer arrays that are not in both arrays, e.g., symmetricdifference({1, 2, 3, 4}, {3, 4, 5, 6}) returns {1, 2, 5, 6}
                               | "union" ; array1 (Any Type), array2 (Any Type); returns all unique elements from the given arrays, e.g., union({1, 2, 3, 4}, {3, 4, 5, 6}) returns {1, 2, 3, 4, 5, 6}, union({"a", "b"}, {"a", "B"}) returns {"a", "b", "B"}

# Example: a!update(data: { 1, 2, 3 }, index: 1, value: 5) returns {5, 2, 3}
# Array functions
# As always in SAIL, none of these mutate the passed data.
array_function_keyword ::= "a!update" ; data (Any Type), index (Number Array, 1-based), value (Any Type); replaces existing values at the specified index or field name and returns the resulting updated data

# Base conversion functions
base_conversion_function_positional ::= "bin2dec" ; binaryValue (Text); returns an Integer
                                      | "bin2hex" ; binaryValue (Text), place (Integer); returns a Text
                                      | "bin2oct" ; binaryValue (Text), place (Integer); returns a Text
                                      | "dec2bin" ; decimalValue (Number), place (Integer); returns a Text
                                      | "dec2hex" ; decimalValue (Number), place (Integer); returns a Text
                                      | "dec2oct" ; decimalValue (Number), place (Integer); returns a Text
                                      | "hex2bin" ; hexValue (Text), place (Integer); returns a Text
                                      | "hex2dec" ; hexValue (Text); returns an Integer
                                      | "hex2oct" ; hexValue (Text), place (Integer); returns a Text
                                      | "oct2bin" ; octValue (Text), place (Integer); returns a Text
                                      | "oct2dec" ; octValue (Text); returns an Integer
                                      | "oct2hex" ; octValue (Text), place (Integer); returns a Text

# Connector functions
connector_function_keyword ::= "a!verifyRecaptcha" ; onSuccess (Save Array) provides fv!score, onError (Save Array) provides fv!error
                             | "a!httpAuthenticationBasic" ; username (Text), password (Encrypted Text), preemptive (Boolean) default false
                             | "a!httpFormPart" ; name (Text), value (Text), contentType (Text, optional, can be set to "auto-detect"), value (Text, optional)
                             | "a!httpHeader" ; name (Text), value (either Text or result of a!scsField())
                             | "a!httpQueryParameter" ; name (Text), value (either Text or result of a!scsField())
                             | "a!scsField" ; externalSystemKey (Text, link to external system in the Third Party Credentials admin console page), fieldKey (Text), usePerUser (Text) default false
                             | "a!wsConfig" ; wsdlUrl (Text), service (Text), port (Text), operation (Text), wsdlCredentials (WsHttpCredentials), endpointcredentials (WsHttpCredentials), extensions (Any Type Array)
                             | "a!wsHttpCredentials" ; username (Text), password (Text), domain (Text)
                             | "a!wsHttpHeaderField" ; name (Text), value (Text)
                             | "a!wsUsernameToken" ; username (Text), password (Text)
                             | "a!wsUsernameTokenScs" ; systemKey (Text), usePerUser (Boolean)

serialization_function_positional ::= "externalize" ; value (Any Type); creates a round-trippable Text from any value, suitable for external storage
                                    | "internalize" ; externalizedText (Text generated by externalize), default (Any Type); only accepts a Text generated by externalize, yielding its original value

# Conversion functions
# Note that SAIL runtime will automatically cast in most cases that do not vary behavior based on type, e.g., "123"+4.5 is 127.5
conversion_function_positional ::= "cast" ; typeNumber (Number or type!reference), value (Any Type); can get the type number by using typeof(value); returns the value cast to given typeNumber
                                 | "displayvalue" ; value (Any Type), arrayToSearch (Any Type Aray), replacement (Any Type Array), default (Text, optional)
                                 | "toboolean" ; value (Any Type); cast to Boolean
                                 | "tocommunity" ; value (Any Type); cast to Community
                                 | "todate" ; value (Any Type); cast to Date
                                 | "todatetime" ; value (Any Type); cast to DateTime
                                 | "todecimal" ; value (Any Type); cast to Double floating-point, e.g., todecimal("3.6") returns 3.6, todecimal("string") returns null
                                 | "todocument" ; value (Any Type); cast to DocumentId
                                 | "toemailaddress" ; value (Any Type); cast to EmailAddress
                                 | "toemailrecipient" ; value (Any Type); cast to EmailRecipient (union of EmailAddress, User and GroupId)
                                 | "tofolder" ; value (Any Type); cast to FolderId
                                 | "tointeger" ; value (Any Type); cast to Integer (32-bit), e.g., tointeger("3","4") returns {3,4}
                                 | "tointervalds" ; value (Any Type); cast to IntervalDS (interval day-to-second)
                                 | "toknowledgecenter" ; value (Any Type); cast to KnowledgeCenterId
                                 | "tostring" ; value (Any Type); cast to Text (string); arrays and complex data are flattened into a single string, e.g., tostring({1,2,3}) returns "1; 2; 3"
                                 | "totime" ; value (Any Type); cast to Time, e.g., totime(datetime(2005,12,13,2,34,56)) returns time(2,34,56)
                                 | "touniformstring" ; value (Any Type); cast to Text (string) uniformly; arrays are cast element by element, retaining original array length, e.g., touniformstring({1,2,3}) returns {"1","2","3"}

# Custom fields functions
custom_fields_function_keyword ::= "a!customFieldConcat" ; fields (Any Type Array)
                                 | "a!customFieldCondition" ; field (record field), operator ("=", "<>", ">", ">=", "<", "<=", "between", "in", "not in", "is null", "not null", "starts with", "not starts with", "ends with", "not ends with", "includes", or "not includes"), value (Any Type)
                                 | "a!customFieldDateDiff" ; startDate (Date or Date and Time), endDate (Date or Date and Time), interval ("DAY" (default), "HOUR", "MINUTE", "SECOND")
                                 | "a!customFieldDefaultValue" ; value (Any Type), default (Any Type)
                                 | "a!customFieldDivide" ; numerator (Number), denominator (Number)
                                 | "a!customFieldLogicalExpression" ; operator (Text, "AND" or "OR"), conditions (A list of a!customFieldLogicalExpression(), a!customFieldCondition(), or both)
                                 | "a!customFieldMatch" ; value (Any Type, this can be accessed in other parameters as fv!value), equals (Any Type), whenTrue (Any Type), then (Any Type), default (Any Type)
                                 | "a!customFieldMultiply" ; value (Number Array)
                                 | "a!customFieldSubtract" ; value1 (Number), value2 (Number)
                                 | "a!customFieldSum" ; value (Number Array)

# Date and time functions
date_time_function_positional ::= "calisworkday" ; date (Date), calendar (Text)
                                | "calisworktime" ; dateTime (DateTime), calendar (Text, optional)
                                | "calworkdays" ; startDate (Date), endDate (Date), calendar (Text)
                                | "calworkhours" ; startDateTime (DateTime), endDateTime (DateTime), calendar (Text, optional)
                                | "date" ; year (Number), month (Number), day (Number)
                                | "datetime" ; year (Number), month (Number), day (Number), hour (Number), minute (Number), second (Number)
                                | "datevalue" ; dateText (Text)
                                | "day" ; date (Date)
                                | "dayofyear" ; date (Date)
                                | "days360" ; startDate (Date), endDate (Date), method (Integer, 1 for European, 0 for US/NASD)
                                | "daysinmonth" ; month (Integer), year (Integer)
                                | "edate" ; startDate (Date), months (Number)
                                | "eomonth" ; startDate (Date), months (Number)
                                | "gmt" ; dateTime (DateTime), timezone (Text, optional, default is context's timezone)
                                | "hour" ; time (Time)
                                | "intervalds" ; hour (Number), minute (Number), second (Number)
                                | "isleapyear" ; year (Number)
                                | "lastndays" ; startDate (Date), numberOfDays (Number)
                                | "local" ; dateTime (DateTime), timezone (Text, optional, default is context's timezone)
                                | "milli" ; dateTime (DateTime)
                                | "minute" ; time (Time)
                                | "month" ; date (Date)
                                | "networkdays" ; startDate (Date), endDate (Date), holidays (Date Array, optional)
                                | "now" ; No parameters
                                | "second" ; time (Time)
                                | "time" ; hour (Number), minute (Number), second (Number), millisecond (Number)
                                | "timevalue" ; timeText (Text)
                                | "timezone" ; No parameters
                                | "timezoneid" ; No parameters
                                | "today" ; No parameters
                                | "weekday" ; date (Date), returnType (Number, optional, 1 correlating 1-7 with Sunday-Saturday, 2 correlating 1-7 with Monday-Sunday, and 3 correlating 0-6 with Monday-Sunday, default is 1)
                                | "weeknum" ; date (Date), methodology (Number, optional, 1 correlating with the week beginning on Sunday and 2 correlating with the week beginning on Monday, default is 1)
                                | "workday" ; startDate (Date), days (Number), holidays (Date Array, optional)
                                | "year" ; date (Date)
                                | "yearfrac" ; startDate (Date), endDate (Date), method (Number, optional, 0 is US(NASD) 30/360, 1 is Actual/Actual, 2 is Actual/360, 3 is Actual/365, 4 is European 30/360, default is 0)

date_time_function_keyword ::= "a!addDateTime" ; startDateTime (DateTime), years (Number, optional), months (Number, optional), days (Number, optional), hours (Number, optional), minutes (Number, optional), seconds (Number, optional), useProcessCalendar (Boolean, optional, default is false), processCalendarName (Text, optional)
                             | "a!subtractDateTime" ; startDateTime (DateTime), years (Number, optional), months (Number, optional), days (Number, optional), hours (Number, optional), minutes (Number, optional), seconds (Number, optional), useProcessCalendar (Boolean, optional, default is false), processCalendarName (Text, optional)

# Evaluation functions
evaluation_function_keyword ::= "a!refreshVariable" ; value (Any Type), refreshAlways (Boolean, optional), refreshInterval (Number, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshAfter (Any Type Array, optional) (suitable for assignment in a!localVariables)
                              | "a!save" ; target (Save Target), value (Any Type) ; provides save!value being saved in value's expression

evaluation_function_mixed ::= "a!localVariables" ; local variables : expression ; provides local!variableName; e.g., a!localVariables(local!x:2, local!y:3, local!x+local!y)
                            | "bind" ; getFunction (Rule or Function Reference), setFunction (Rule or Function Reference) (bind only available for variables defined by load)
                            | "load" ; persisted local variables : expression ; provides local!variableName; e.g., load(local!x:2, local!y:3, local!x+local!y), prefer a!localVariables
                            | "with" ; transient local variables : expression ; provides local!variableName; e.g., with(local!x:2, local!y:3, local!x+local!y), prefer a!localVariables

# Informational functions
informational_function_positional ::= "error" ; errorMessage (Text); throws an exception
                                    | "infinity" ; No parameters (constant)
                                    | "isinfinite" ; number (Number)
                                    | "isnegativeinfinity" ; number (Number)
                                    | "isnull" ; value (Any Type)
                                    | "ispositiveinfinity" ; number (Number)
                                    | "nan" ; No parameters (constant)
                                    | "null" ; No parameters
                                    | "runtimetypeof" ; value (Any Type); drills into unions to return the underlying type
                                    | "typename" ; typeNumber (Number); suitable for display, not for comparison
                                    | "typeof" ; value (Any Type); returns the type number of the value
                                    | "a!automationId" ; automationTypes (Text Array)
                                    | "a!defaultValue" ; value (Any Type), default (Any Type); returns the first non-null non-empty parameter
                                    | "a!isNotNullOrEmpty" ; value (Any Type)
                                    | "a!keys" ; map (Map)
                                    | "a!listType" ; listOf (Type); returns the list type number of the non-list type parameter

informational_function_keyword ::= "a!automationType" ; automationIds (Integer Array, valid values include 1 for "NONE", 2 for "RPA", 3 for "AI", 4 for "INTEGRATION", 5 for "OTHER")
                                 | "a!isNullOrEmpty" ; value (Any Type)
                                 | "a!submittedOfflineTaskIds" ; No parameters

# Logical functions - Boolean operations and conditional logic
logical_function_positional ::= | "true" ; No parameters
                                | "false" ; No parameters
                                | "and" ; value1 (Boolean), value2 (Boolean), ... (variadic Boolean parameters); remember, `and` is only a function, not an operator; short-circuits
                                | "or" ; value1 (Boolean), value2 (Boolean), ... (variadic Boolean parameters); remember, `or` is only a function, not an operator; short-circuits
                                | "not" ; booleanValue (Boolean)
                                | "if" ; condition (Boolean), valueIfTrue (Any Type), valueIfFalse (Any Type); short-circuits
                                | "choose" ; index (Number, 1-based), choice1 (Any Type), choice2 (Any Type), ... (variadic choices); short-circuits

# Example use of a!match
# a!localVariables(
#   local!casePriority: "Medium",
#   a!match(
#     value: local!casePriority,
#     equals: "Low",
#     then: a!stampField(
#       labelPosition: "COLLAPSED",
#       icon: "angle-down",
#       contentColor: "STANDARD"
#     ),
#     equals: "Medium",
#     then: a!stampField(
#       labelPosition: "COLLAPSED",
#       icon: "angle-up",
#       contentColor: "STANDARD"
#     ),
#     equals: "High",
#     then: a!stampField(
#       labelPosition: "COLLAPSED",
#       icon: "angle-double-up",
#       contentColor: "STANDARD",
#       backgroundColor: "NEGATIVE"
#     ),
#     default: "No Priority"
#   )
# )

logical_function_mixed ::= "a!match" ; value (Any Type), equals (Any Type), then (Any Type), ... (repeated equals/then pairs), default (Any Type, optional); this is a case style match selection

# Looping functions - Iteration and data processing
# apply, reduce looping functions cannot be used to generate interface components; use a!forEach instead
looping_function_positional ::= "apply" ; function (Rule or Function reference), array (Any Type Array), context ... (variadic parameters passed directly into each predicate evaluation); same concept as functional map
                               | "reduce" ; function (Rule or Function reference), initial (Any Type), list (Any Type Array), context ... (variadic parameters passed directly into each predicate evaluation)
                               | "reject" ; array (Any Type Array), expression (Function) ; provides fv!index, fv!item

# Predicate Looping functions
# filter(a!isNotNullOrEmpty, {1, 2, null, 3, null, 4}) would return {1, 2, 3, 4}
predicate_looping_function_positional ::= "all" ; predicate (Rule or Function reference), list (Any Type Array), context ... (variadic parameters passed directly into each predicate evaluation); short-circuits
                               | "any" ; predicate (Rule or Function reference), list (Any Type Array), context ... (variadic parameters passed directly into each predicate evaluation); short-circuits
                               | "none" ; predicate (Rule or Function reference), list (Any Type Array), context ... (variadic parameters passed directly into each predicate evaluation); short-circuits
                               | "filter" ; predicate (Rule or Function reference), list (Any Type Array), context ... (variadic parameters passed directly into each predicate evaluation); short-circuits

# Example of nested a!forEach:
#
# a!forEach(
#    items: {"January", "February", "March"},
#    expression: a!localVariables(
#      local!month: fv!item,
#      a!forEach(
#        items: {1, 15},
#        expression: local!month & " " & fv!item
#      )
#    )
#  )
#
# Generates a 3-item list: {"January 1", "January 15"}, {"February 1", "February 15"}, and {"March 1", "March 15"}
# a!forEach does work with interface components
looping_function_mixed ::= "a!forEach" ; items (Any Type Array), expression (deferred expression expressed inline) ; provides fv!item (Any Type) as the current item, fv!index (Integer) as current item's index in array, v!isFirst (Boolean) true for first item in array, fv!isLast (Boolean) true for last item in array, fv!itemCount (Integer) total count of array items including nulls, fv!identifer (Any Type Array) only provided if items is a DataSubset with identifiers

# Mathematical functions - Numeric calculations and operations
# reminder that these truncation and rounding operations operate on double precision floating point, so may not be exact
mathematical_function_positional ::= "abs" ; number (Number); e.g., abs(-2.0) returns 2.0
                                    | "ceiling" ; number (Number), significance (Number, optional default is 1.0); e.g., ceiling(7.32,.5) returns 7.5
                                    | "combin" ; n (Number), m (Number); number of unique ways to choose m elements from a pool of n elements
                                    | "e" ; No parameters (constant)
                                    | "enumerate" ; n (Integer); returns 0 through n-1, e.g., enumerate(3) returns {0,1,2}, enumerate(3)+1 returns {1,2,3}
                                    | "even" ; number (Number); positive numbers up to nearest even integer, negative numbers down to the nearest even integer
                                    | "exp" ; power (Number); e raised to power
                                    | "fact" ; number (Number, between 0 and 170); factorial, e.g., fact(6) returns 720
                                    | "factdouble" ; number (Number); double factorial of number (mathematically n!!), e.g., factdouble(6) returns 48
                                    | "floor" ; number (Number), significance (Number, optional default is 1.0); e.g., floor(-7,5) returns -10
                                    | "int" ; number (Number); rounds number down to nearest integer
                                    | "ln" ; number (Number); natural log
                                    | "log" ; number (Number), base (Number, optional, default is 10)
                                    | "mod" ; dividend (Number), divisor (Number); remainder of dividend when divided by the divisor; reminder, there is no mod operator, only mod function
                                    | "mround" ; number (Number), multiple (Number); rounds number to specified multiple, e.g., mround(63,8) returns 64
                                    | "multinomial" ; number (Integer Array); adds the specified integers and divides the factorial of the sum by the factorial of the individual numbers, e.g., multinomial({2,3,4}) returns 1260
                                    | "odd" ; number (Number); rounds positive number up to nearest odd integer and negative number down to nearest odd integer
                                    | "pi" ; No parameters (constant)
                                    | "power" ; base (Number), exponent (Number); base raised to exponent, e.g., power(2, 8) returns 256.0
                                    | "product" ; factor (Number Array); returns product of specified numbers, e.g., product(2,3,4) returns 24
                                    | "quotient" ; numerator (Number), denominator (Number); returns the quotient when numerator is divided by the denominator, and drops the remainder, e.g., quotient(8.0,3.0) returns 2
                                    | "rand" ; No parameters; returns a single random primitive double number
                                    | "rand" ; count (Number); returns an array of given count size filled with random double numbers
                                    | "round" ; number (Number), digits (Number, optional, default is 2)
                                    | "rounddown" ; number (Number), digits (Number, optional, default is 2)
                                    | "roundup" ; number (Number), digits (Number, optional, default is 2)
                                    | "sign" ; number (Number); returns 1 for positive, -1 for negative, 0 for 0
                                    | "sqrt" ; number (Number); returns square root of number, e.g., sqrt(25) returns 5.0
                                    | "sqrtpi" ; number (Number); multiplies by constant pi then returns square root, e.g., sqrtpi(2.25) returns 2.658681
                                    | "sum" ; addend (Number Array); returns sum of array, e.g., sum({1,2,3,4}) returns 10
                                    | "sumsq" ; number (Number Array); squares each number in array then returns its sum, e.g., sumsq(3,4) returns 25
                                    | "trunc" ; value (Number), numberOfDecimals (Number, optional default is 0); truncates to number of decimal places

mathematical_function_keyword ::= "a!distanceBetween" ; startLatitude (Number), startLongitude (Number), endLatitude (Number), endLongitude (Number); returns distance between two locations in meters, e.g., a!distanceBetween(startLatitude: 38.932290, startLongitude: -77.218490, endLatitude: 38.917370, endLongitude: -77.220760) returns 1670.609

# User or GroupId functions - User and group management
# These provide access to data about users and groups; the people type is a union of users and groups, able to hold either
people_function_positional ::= "getdistinctusers" ; peopleArray (UserOrGroupId Array)
                             | "isusernametaken" ; username (Text)
                             | "loggedInUser" ; No parameters (returns currently logged in username)
                             | "togroup" ; value (Number); convert a number to a GroupId
                             | "topeople" ; value (Any Type); convert a text or User to UserOrGroupId union holding User or integer or GroupId to UserOrGroupId union holding GroupId
                             | "touser" ; value (Text); convert a text to User
                             | "group" ; groupId (Number), property (Text); properties include created, creator, groupName, groupTypeName, lastModified, parentName, delegatedCreation, description, id, memberPolicyName, parentId, securityMapName, viewingPolicyName
                             | "user" ; username (Text), property (Text); properties include firstName, middleName, lastName, displayName (the user's nickname), supervisorName, titleName, email, phoneOffice, phoneMobile, phoneHome, address1, address2, address3, city, state, province, zipCode, country, locale, timeZone, uuid, created, status, userTypeId, userTypeName
                             | "supervisor" ; username (User)
                             | "a!isUserMemberOfGroup" ; username (User), groups (GroupId Array), matchAllGroups (Boolean, false matches any group, true must match all groups)
                             | "a!doesGroupExist" ; groupId (GroupId); returns Boolean

people_function_keyword ::= "a!groupMembers" ; groupId (GroupId), direct (Boolean, true for only direct members default is false), memberType (Text, "ALL" (default), "GROUP", or "USER"), pagingInfo (PagingInfo); returns DataSubset
                          | "a!groupsByName" ; groupName (Text); cannot return system groups; returns GroupId Array
                          | "a!groupsByType" ; groupType (Text), pagingInfo (PagingInfo); returns DataSubset
                          | "a!groupsForUser" ; username (User), isGroupAdministrator (Boolean), groupTypes (GroupType array); returns GroupId Array
                          | "getgroupattribute" ; group (GroupId), attribute (Text); e.g., getgroupattribute(local!myGroup,"dateCreated")

# STANDARD ICONS LIST FOR REFERENCE
# Icons can be used in components like a!buttonWidget, a!stampField, a!richTextIcon, etc.
# Common icons include: "ADD", "ARCHIVE", "ARROW_LEFT", "ARROW_RIGHT", "ATTACHMENT", "BANK", "BAR_CHART", "BOOK", 
# "BRIEFCASE", "BUILDING", "CALENDAR", "CAR", "CHART", "CHEVRON_DOWN", "CHEVRON_LEFT", "CHEVRON_RIGHT", "CHEVRON_UP",
# "CLIPBOARD", "CLOCK", "CLOUDY", "COMPOSE", "CURRENCY_DOLLAR", "DELETE", "DOCUMENT", "DOWNLOAD", "EDIT", "EMAIL",
# "ENVELOPE", "EXIT", "EYE", "FILE", "FILTER", "FOLDER", "GEAR", "GLOBE", "HOME", "HOURGLASS", "INFO", "KEY",
# "LIGHT_BULB", "LINK", "LIST", "LOCK", "MAGNIFY", "MENU", "MICROPHONE", "MINUS", "MORE", "PADLOCK", "PAPER_AIRPLANE",
# "PAUSE", "PEN", "PENCIL", "PEOPLE", "PERSON", "PHONE", "PICTURE", "PIE_CHART", "PLAY", "PLUS", "PRINT", "QUESTION",
# "REFRESH", "REPLY", "SAVE", "SEARCH", "SETTINGS", "SHARE", "SHOPPING_CART", "STAR", "STOP", "THUMBS_DOWN", "THUMBS_UP",
# "TIME", "TRASH", "UMBRELLA", "UNDO", "UPLOAD", "USER", "VIDEO", "WARNING", "WRENCH", "ZOOM_IN", "ZOOM_OUT"

# Scripting functions - System and utility functions
# Date/time functions beginning with "user" pay attention to the current user's context (e.g., user's calendar)
scripting_function_positional ::= "a!isPageWidth" ; pageWidths (Text Array); true if the interface is being viewed on a page that falls within the specified width ranges; valid values: "PHONE", "TABLET_PORTRAIT", "TABLET_LANDSCAPE", "DESKTOP_NARROW", "DESKTOP", "DESKTOP_WIDE"
                                 | "averagetaskcompletiontimeforprocessmodel" ; processModel (ProcessModelId), includeSubProcessData (Boolean)
                                 | "averagetasklagtimeforprocessmodel" ; processModel (ProcessModelId), includeSubProcessData (Boolean)
                                 | "averagetaskworktimeforprocessmodel" ; processModel (ProcessModelId), includeSubProcessData (Boolean)
                                 | "community" ; communityId (Number), property (Text); valid properties include dateCreated, description, id, name, numberOfDocuments, parentId, parentName, active
                                 | "document" ; documentId (Number), property (Text); valid properties include dateCreated, description, expirationDate, extension, folderId, folderName, id, knowledgeCenterId, knowledgeCenterName, lastUserToModify, lockedBy, name, totalNumberOfVersions, pendingApproval, size (in bytes), approved, changesRequireApproval, url, e.g., document(101, "expirationDate")
                                 | "folder" ; folderId (Number), property (Text); valid properties include changesRequireApproval, creator, dateCreated, documentChildren, folderChildren, id, inheritSecurityFromParent, knowledgeCenterId, knowledgeCenterName, knowledgeCenterSearchable, name, numberOfDocuments, parentFolderId, parentFolderName, pendingApproval, searchable
                                 | "isInDaylightSavingTime" ; dateTime (Date or DateTime), timeZoneId (Text)
                                 | "knowledgecenter" ; knowledgeCenterId (Number), property (Text); valid properties include autoApproveForReadOnlyAccess, changesRequireApproval, communityId, communityName, creator, dateCreated, description, expirationDays, id, isSearchable, name, numberOfDocuments, size, type
                                 | "numontimeprocessesforprocessmodel" ; processModel (ProcessModelId), includeSubProcessData (Boolean)
                                 | "numontimetasksforprocessmodel" ; processModel (ProcessModelId), includeSubProcessData (Boolean)
                                 | "numoverdueprocessesforprocessmodel" ; processModel (ProcessModelId), includeSubProcessData (Boolean)
                                 | "numoverduetasksforprocessmodel" ; processModel (ProcessModelId), includeSubProcessData (Boolean)
                                 | "numprocessesforprocessmodelforstatus" ; processModel (ProcessModelId), status (Text one of "active", "cancelled", "completed", "paused", "problem"), includeSubProcessData (Boolean)
                                 | "numtasksforprocessmodelforstatus" ; processModel (ProcessModelId), status (Text), includeSubProcessData (Boolean)
                                 | "offsetFromGMT" ; date (Date), timeZoneId (Text); offset (in minutes) from GMT of the given date and timezone
                                 | "repeat" ; numberOfTimes (Number), value (Any scalar Type); e.g., repeat(2, "hello") returns {"hello", "hello"}
                                 | "torecord" ; xml (Text formatted as XML), variableOfTargetType (Any Type); converts XML to a value of variableOfTargetType's type
                                 | "toxml" ; value (Any Type), format (Boolean), name (Text for root element), namespace (Text, optional default namespace in result XML)
                                 | "userdate" ; year (Number), month (Number), day (Number); e.g., datetext(userdate(1427,8,18),mm/dd/yyyy) returns 8/18/1427; returns Date
                                 | "userdatetime" ; year (Number), month (Number), day (Number), hour (Number), minute (Number), second (Number); return DateTime
                                 | "userdatevalue" ; dateText (Text); returns Date representing the given dateText
                                 | "userday" ; date (DateTime); returns day of the month
                                 | "userdayofyear" ; date (Date); returns number of day within year
                                 | "userdaysinmonth" ; month (Number), year (Number); returns the number of days in given month
                                 | "useredate" ; startDate (Date), months (Number); date that is the number of months before or after the given starting date in the user preferred calendar
                                 | "usereomonth" ; startDate (Date), months (Number); date for the last day of the month that is the number of months before or after the given starting date in the user preferred calendar
                                 | "userisleapyear" ; year (Number); returns Boolean
                                 | "userlocale" ; user (User); returns local of given user, e.g., "es_MX"
                                 | "usermonth" ; date (Date or DateTime); returns month from given date or datetime
                                 | "usertimezone" ; user (User); returns timeone of given user, e.g., "GMT"
                                 | "userweekday" ; date (Date), type (Number, optional; 1 is 1-7 from Sun-Sat (default), 2 is 1-7 for Mon-Sun, 3 is 0-6 for Mon-Sun)
                                 | "userweeknum" ; date (Date), methodology (Number, optional; 1 week begins on Sun (default), 2 on Mon, 3 on Tue, 4 on Wed, 5 on Thur, 6 on Fri, 7 on Sat)
                                 | "useryear" ; date (Date or Date and Time)
                                 | "datetext" ; date (Date), format (Text); see format for datetext, e.g., datetext(datetime(2025, 6, 17, 0, 3, 14, 159), "yyyy/MM/dd") is "2025/06/17"
                                 | "urlwithparameters" ; url (Text), parameterNames (Text array), parameterValues (Text array); build a URL; the parameterNames and parameterValues must be same length

# format for datetext (similar to Excel and Java's date and time formatting)
# repeating format codes can alter length of output, e.g., EEEE would be Tuesday instead of E's Tue, ddd would be 017 instead of d's 17
# Format Code (case sensitive)| Date or Time Component| Presentation| Examples for datetime(2025, 6, 17, 0, 3, 14, 159)
# G | Era designator| Text| AD
# y | Year| Year| 2025
# Y | Week Year| Year| 2025
# M | Month in year| Month| 6
# w | Week in year | Number | 25
# W | Week in month | Number | 3
# D | Day in year | Number | 168
# d | Day in month | Number | 17
# F | Day of week in month | Number | 3
# E | Day name in week | Text | Tue
# a | Am/pm marker | Text | AM
# H | Hour in day (0-23) | Number | 0
# k | Hour in day (1-24) | Number | 24
# K | Hour in am/pm (0-11) | Number | 0
# h | Hour in am/pm (1-12) | Number | 12
# m | Minute in hour | Number | 3
# s | Second in minute | Number | 14
# S | Millisecond | Number | 1
# z | Time zone | General time zone | GMT
# Z | Time zone | RFC 822 time zone | +0000

scripting_function_keyword ::= "a!isNativeMobile" ; No parameters; returns true if being viewed within the Appian for Mobile application
                             | "a!portalUrlWithLocale" ; locale (Text); e.g., "en_US" for English (United States)
                             | "a!urlForPortal" ; portalPage (Reference to portal page in portal!domain), urlParameters (Map), locale (Text)
                             | "a!urlForRecord" ; recordType (RecordType), targetLocation ("TEMPO" or site reference), identifier (Text), view (Text, optional, default is "summary")
                             | "a!urlForSite" ; sitePage (SitePage), urlParameters (Map)
                             | "a!urlForTask" ; taskIds (Number, Task IDs of process tasks to generate links), returnTaskPathOnly (Boolean, If true, only the last path segment to the task is included; if false, the full URL of the task is returned. Default: false)
                             | "webservicequery" ; config (WsConfig), data (Dictionary); invokesweb service configured by WsConfig with supplied input data, yielding a WsResult object with result object and HTTP status code of response; use only for READ-ONLY web services to avoid side effects
                             | "xpathdocument" ; docId (DocumentId), expression (Text in form of XPath Expression), prefix (Text if XML document has default namespace)
                             | "xpathsnippet" ; xmlSnippet (Text), xpath (Text), prefix (Text, optional); e.g., xpathsnippet("<name>John Smith</name>", "//name/text()") returns John Smith

# Statistical functions - Data analysis and statistical calculations
statistical_function_positional ::= "avedev" ; number (Number Array); average deviation
                                   | "average" ; number (Number Array); mean average
                                   | "count" ; value1 (Any Type Array), value2 (Any Type Array), ... (variadic Any Type parameters); returns sum of length (count) of all arrays
                                   | "frequency" ; dataArray (Number Array), binsArray (Number Array); returns Integer Array, uses the bin array to create groups bounded by the elements of the array, e.g., frequency({64,74,75,84,85,86,95},{70,79,89}) returns {1,2,3,1}
                                   | "gcd" ; number (Number Array); returns greatest common denominator of given non-negative number(s), e.g., gcd({4,12,36}) returns 4
                                   | "geomean" ; number (Number Array); geometric mean, e.g., geomean({4,9}) returns 6
                                   | "harmean" ; number (Number Array); harmonic mean, e.g., harmean({1,2,3}) returns 1.636364
                                   | "lcm" ; number (Number Array); least common multiple of given non-negative number(s), e.g., lcm({5,10,15}) returns 30
                                   | "lookup" ; lookupWithin (Any Type Array), dataToLookup (Any Type), valueIfNotPresent (Any Type), returns index integer, e.g., lookup({"a", "b", "c", "d"}, "c", -1)
                                   | "max" ; number (Number Array); e.g., max({1,2,3,4}) returns 4
                                   | "median" ; number (Number Array); median
                                   | "min" ; number (Number Array); minimum of given numbers, e.g., min({1,2,3,4}) returns 1
                                   | "mode" ; number (Number Array); mode, e.g., mode(1,2,2,3,3,3,4) returns 3
                                   | "rank" ; number (Number), array (Number Array), order (Boolean, optional, false for high to low and true for low to high); integer representing rank of given number in the specified array, e.g., rank(2,{1,2,3,4},0) returns 3
                                   | "stdev" ; number (Number Array); standard deviation of sample, e.g., stdev(1,2,3,4) returns 1.290994
                                   | "stdevp" ; number (Number Array); standard deviation of population (assuming that the numbers form the entire data set and not just a sample), e.g., stdevp(1,2,3,4) returns 1.118034
                                   | "var" ; number (Number Array); variance of sample, e.g., var(1,2,3,4) returns 1.666667
                                   | "varp" ; number (Number Array); variance of population (assuming that the numbers form the entire data set and not just a sample), e.g., varp(1,2,3,4) returns 1.25

# Data Builders - Functions for creating structured data objects
data_builder_function_positional ::= "todatasubset" ; arrayToPage (Any Type Array), pagingConfiguration (PagingInfo); returns a DataSubset
                                   | "topaginginfo" ; startIndex (Number), batchSize (Number); returns a PagingInfo

data_builder_function_keyword ::= "a!dataSubset" ; startIndex (Number), batchSize (Number), sort (SortInfo Array, optional), totalCount (Integer), data (Any Type Array), identifiers (Any Type Array, optional, of same length as data); returns a DataSubset, a slice of data within a larger dataset, such as an individual page of data from among many pages, e.g., a!dataSubset(startIndex: 1, batchSize: 4, sort: a!sortInfo(field: "name", ascending: true()), totalCount: 10, data: {"a", "b", "c", "d"}, identifiers: {1, 2, 3, 4})
                                | "a!pagingInfo" ; startIndex (Number), batchSize (Number), sort (SortInfo Array, optional); returns a PagingInfo; e.g., a!pagingInfo(startIndex: 1,batchSize: 4,sort: a!sortInfo(field: "name",ascending: true()))

# System functions - Core system operations and utilities
system_function_keyword ::= "a!aggregationFields" ; groupings (type generated by a!grouping), measures (type generated by a!measure)
                          | "a!applyValidations" ; recordField (Type Record Field), context (Any Type), additionalValidations (Text Array)
                          | "a!documentFolderForRecordType" ; recordType (RecordType)
                          | "a!endsWith" ; text (Text), endsWithText (Text) ; e.g., a!endsWith(text: "Appian", endsWithText: "n") returns true
                          | "a!entityData" ; entity (DataStoreEntity), data (Any Type Array); returns an EntityData, suitable for use in a!writeToMultipleDataStoreEntities()
                          | "a!entityDataIdentifiers" ; entity (Data Store Entity), identifiers (Any Type array); returns an EntityDataIdentifiers
                          | "a!executeStoredProcedureForQuery" ; dataSource (Text), procedureName (Text), inputs (StoredProcedureInput Array, optional), timeout (Number in seconds, optional), autoCommit (Boolean, default false); returns an a!map(success, error, results, parameters)
                          | "a!httpResponse" ; statusCode (Number, default is 200), headers (HttpHeader Array, optional, built from  a!httpheader()), body (Text, optional or DocumentId)
                          | "a!integrationError" ; title (Text), message (Text), detail (Text, optional); fv!success, fv!error, and fv!result can be used to get response values from any errors
                          | "a!isBetween" ; value (Number), upperLimit (Number), lowerLimit (Number); e.g., a!isBetween(value: 4, lowerLimit: 1, upperLimit: 6) returns true
                          | "a!isInText" ; text (Text), subtext (Text); returns true if subtext is contained within the text parameter, e.g., a!isInText(text:"I love low-code",subtext: "low-code") returns true
                          | "a!listViewItem" ; title (Text, name or short text description), details (Text, longer text description), image (DocumentId or User, optional), timestamp (DateTime, creation or modification timestamp); returns a ListViewItem
                          | "a!pageResponse" ; data (Any Type, in the integration response, the path of the data returned from the integration), nextPage (Text, path of the next page of results within the header or body of the response. This could be a URL, URI, cursor, or token); returns Variant Array
                          | "a!query" ; selection (Selection, optional), aggregation (Aggregation), logicalExpression (LogicalExpression), filter (QueryFilter), pagingInfo (PagingInfo); returns a Query
                          | "a!queryAggregation" ; aggregationColumns (AggregationColumn Array); returns an Aggregation
                          | "a!queryAggregationColumn" ; field (Text), alias (Text), visible (Boolean), isGrouping (Boolean), aggregationFunction (Text, optional, one of "COUNT", "SUM", "AVG", "MIN" or "MAX" and requires isGrouping be false), groupingFunction (Text, optional, one of "YEAR", "MONTH", requires isGrouping be true, requires field's data be DateTime or Date); returns an AggregationColumn for use inside an Aggregation
                          | "a!queryColumn" ; field (Text), alias (Text, optional), visible (Boolean); returns a Column
                          | "a!queryEntity" ; entity (Data Store Entity), query (Query), fetchTotalCount (Boolean, default false; false improves performance by avoiding running query to retrieve total); returns a DataSubset
                          | "a!queryFilter" ; field (Any Type, must be from recordType! domain), operator (Text, must be one of "=", "<>", ">", ">=", "<", "<=", "between", "in", "not in", "is null", "not null", "starts with", "not starts with", "ends with", "not ends with", "includes", "not includes", "search"), value (Any Type), applyWhen (Boolean, optional, default is true, false avoids running filter)
                          | "a!queryLogicalExpression" ; operator (Text, must be one of "AND", "OR", or "AND_ALL"), logicalExpressions (LogicalExpression array), filters (QueryFilter Array), ignoreFiltersWithEmptyValues (Boolean, optional, default false); returns a LogicalExpression
                          | "a!queryProcessAnalytics" ; report (DocumentId), query (Query, optional), contextGroups (GroupId Array), contextProcessIds (ProcessId Array), contextProcessModels (ProcessModelId Array), contextUsers (User Array)
                          | "a!queryRecordByIdentifier" ; recordType (RecordType), identifier (Any Type), fields (Any Type Array, must be from recordType! domain, optional), relatedRecordData (RelatedRecordData Array, generated from a!relatedRecordData())
                          | "a!queryRecordType" ; recordType (RecordType), fields (Any Type Array, must be from recordType! domain, optional), filters (Any Type Array, optional), pagingInfo (PagingInfo), fetchTotalCount (Boolean), relatedRecordData (RelatedRecordData Array, from a!relatedRecordData())
                          | "a!querySelection" ; columns (Column Array from a!queryColumn())
                          | "a!recordData" ; recordType (RecordType), filters (Any Type Array, optional), relatedRecordData (RelatedRecordData array), fields (Any Type Array, must be from recordType! domain, optional)
                          | "a!recordFilterChoices" ; choiceLabels (Text Array), choiceValues (Any Type Array); e.g., a!recordFilterChoices(choiceLabels: {"Active", "Inactive"}, choiceValues: {1, 0})
                          | "a!recordFilterDateRange" ; name (Text), field (RecordField), isVisible (Boolean, optional), defaultFrom (Date, optional), defaultTo (Date, optional)
                          | "a!recordFilterList" ; name (Text), options (FacetOption Array), defaultOption (Text, optional), isVisible (Boolean, optional), isRequired (Boolean, optional), allowMultipleSelections (Boolean, optional, default is true)
                          | "a!recordFilterListOption" ; id (Integer, must be unique across other filter options witin same user filter), name (Text), filter (QueryFilter), dataCount (Integer, defines how many items in the data set will be selected if this filter option is selected)
                          | "a!relatedRecordData" ; relationship (RecordType Relationship), limit (Integer), sort (SortInfo Array), filters (Any Type Array, optional)
                          | "a!startsWith" ; text (Text), startsWithText (Text) ; e.g., a!startsWith(text: "Appian", startsWithText: "A") returns true
                          | "a!storedProcedureInput" ; name (Text), value (Any Type); creates an input to be passed to a!executeStoredProcedureOnSave() or a!executeStoredProcedureForQuery(), e.g., a!storedProcedureInput(name: "customer_id", value: 123); returns a Map
                          | "a!userRecordIdentifier" ; users (User Array); returns a Record Identifier Array

# a!iconNewsEvent color list:
# BLUE, GREEN, GREY, ORANGE, PURPLE, RED

# a!iconNewsEvent icon list:
# ADD_PERSON, AIRPLANE, ARCHIVE, ATTACHMENT, BANK, BAR_CHART, BARCODE, BOOK, BRIEFCASE, BUILDING, CALENDAR, CAR, CHEVRONS, CLIPBOARD, CLOCK,
# CLOUDY, COMPOSE, CONVERSATION, CREDIT_CARD, CROSSOVER, CURRENCY_DOLLAR, CURRENCY_EURO, CURRENCY_POUND, CURRENCY_YEN, DELETE, DISCS, DOCUMENT,
# DOWNLOAD, ENVELOPE, EXIT, EYE, FACTORY, FILE_CABINET, FILE_DOC, FILE_DOCX, FILE_PDF, FILE_PPT, FILE_PPTX, FILE_XLS, FILE_XLSX, FOLDER,
# FOUNTAIN_PEN, GEAR, GEARS, GLOBE, HAMMER, HANDSHAKE, HOME, HOURGLASS, ID_CARD, KEY, LIFE_PRESERVER, LIGHT_GLOW, LIGHTNING, LINE_CHART, LINE_CHART_UP,
# LIST, MAGNIFY, MEDAL, MICROPHONE, MUSIC_NOTE, PADLOCK, PAINT_ROLLER, PAPER_AIRPLANE, PARTLY_CLOUDY, PAUSE, PEN, PENCIL, PEOPLE_2, PEOPLE_3, PEOPLE_4,
# PERSON, PERSON_INFO, PIE_CHART, PIGGY, PLAY, PLUS, PRESENTATION, PROCESS, QUESTION_BOX, QUESTION_BUBBLE, QUESTION_CIRCLE, REFRESH, REMOVE_PERSON,
# REPLY_ALL, REPLY, RETURN, RIBBON, ROAD_SIGN_CURVES, ROAD_SIGN_TURN, ROCKET, SCALE, SHARE, SHOPPING_CART, SIGN_POST, SIGNATURE, SMART_PHONE,
# SPEECH_BUBBLE, SPEECH_BUBBLE_DOTS, SPINNER, STEPS, STOP, STORMY, SUITCASE, SUN, TABLE, TARGET, TASK, TASK_BIG, TASK_PROBLEM, THUMBS_DOWN, THUMBS_UP,
# TRAFFIC_CONE, TROPHY, UMBRELLA, VIDEO, WARNING, WHEELCHAIR, WRENCH, ZOOM_IN, ZOOM_OUT

# Sample a!jsonPath usage:
# a!localVariables(
#    local!testData: "{
#  ""store"":""Widget Central"",
#  ""items"":[
#  {
#  ""id"":1,
#  ""name"":""first-object"",
#  ""category"":""cheap"",
#  ""price"":5.50
#  },
#  {
#  ""id"":2,
#  ""name"":""second-object"",
#  ""category"":""cheap"",
#  ""price"":15.50
#  }
#  ]
#  }",
#    a!jsonPath(local!testData, "items[0]")
#  )
# returns the Text represented by {"price":5.5,"name":"first-object","id":1,"category":"cheap"}

system_function_positional ::=  "a!deployment" ; deploymentUuid (Deployment), property (Text); valid properties include "name", "description","uuid","auditUuid","status","applications","packageType","objectsPackageId","customizationFileId","databaseScriptsIds","pluginsPackageId","logId","source","target","objectsDeployed","objectsFailed","requester","reviewer","reviewerComment","decision"
                              | "a!doesUserHaveAccess" ; fields (reference to one or more record fields from recordType! domain, e.g., recordType!Employee.fields.birthDate)
                              | "a!fromJson" ; jsonText (Text); returns value corresponding to the given jsonText
                              | "a!getDataSourceForPlugin" ; dataSourceConnectedSystem (Any Type references a Data Source Connected System value)
                              | "a!iconIndicator" ; icon (Text); returns a DocumentId, suitable for a!httpResponse() or a!documentImage()
                              | "a!iconNewsEvent" ; icon (Text), color (Text); returns a documentId, suitable for a!httpResponse() or a!documentImage()
                              | "a!jsonPath" ; value (Text representing value to be queried), expression (Text the JSONPath query to be run against value); returns Text
                              | "a!latestHealthCheck" ; No parameters
                              | "a!sentimentScore" ; text (Text); returns a list of scores representing the emotional or subjective sentiment expressed in each of the provided text values, ranging from 1.0 (positive) to -1.0 (negative)
                              | "a!sortInfo" ; field (Text), ascending (Boolean, optional), e.g., a!sortInfo(field: "lastName", ascending: false)
                              | "a!storedProcedureInput" ; name (Text), value (Any Type)
                              | "a!submitUploadedFiles" ; documents (DocumentId Array), onSuccess (Save Array), onError (Save Array); only for use in saveInto parameter of a button or link; returns Any Type
                              | "a!toJson" ; value (Any Type), removeNullOrEmptyFields (Boolean, default is false); converts a value into a JSON string, e.g., a!toJson(a!map(first:"Brian", last:"Sullivan")) returns {"first":"Brian","last":"Sullivan"}
                              | "a!toRecordIdentifier" ; recordType (RecordType), identifier (Any Type Array, Individual record IDs within the record type)
                              | "a!userRecordFilterList" ; No Parameters, Returns the default user filters for the User record type. For use in the User record type only
                              | "a!userRecordListViewItem" ; record (User, reference to the current User record, provided via rv!record); returns a ListViewItem

system_function_mixed ::= "a!map" ; key1 (Text), value1 (Any Type), key2 (Text), value2 (Any Type), ... (variadic key-value pairs); constructs a value of type Map composed of given keys mapped to given values, e.g., a!map(first:"Brian", last:"Sullivan", age:123) yields a value of type Map with keys "first", "last" and "age"; keywords must be distinct; prefer maps over dictionaries, they will cast

# Text functions - String manipulation and formatting
# When formatting double numbers, prefer to use either fixed or a currency formatting function
text_function_positional ::= "cents" ; number (Number), decimals (Number), e.g., cents(123412) returns 123,412.00¢
                            | "char" ; number (Number); number into its Unicode character equivalent, e.g., char(65) returns "A", char(10) returns a newline
                            | "charat" ; text (Text), index (Number, 1-based); character at given index within specified string
                            | "clean" ; text (Text); returns specified text, minus any characters not considered printable
                            | "cleanwith" ; text (Text), charactersToAllow (Text); specified text, minus any characters not in charactersToAllow, e.g., cleanwith("text string","x t") returns "txt t"
                            | "code" ; text (Text); text into Unicode integers, e.g., code("Convert to Unicode") returns {67, 111, 110, 118, 101, 114, 116, 32, 116, 111, 32, 85, 110, 105, 99, 111, 100, 101}
                            | "concat" ; text1 (Text), text2 (Text), ... (variadic Text parameters); concanates given text strings into one string, without a separator; see & operator
                            | "exact" ; left (Any Type), right (Any Type); compares left against right exactly; can compare text against text case sensitively, array contents against array contents, etc., but cannot safely compare a null
                            | "extract" ; text (Text), startDelimiter (Text), endDelimiter (Text); the value (or values, if the text contains multiple delimited values) between the delimiters from the given text, e.g., extract("start function /\*extract this\*/ end function","/\*","\*/") returns "extract this"
                            | "find" ; search_text (Text), within_text (Text), start_num (Number, optional, based at 1); Searches the text for a particular substring, returning the positional index of the first character of the first match, e.g., find("to", "boston") returns 4
                            | "fixed" ; number (Number), decimals (Number, optional), no_commas (Boolean, optional, default is false); rounds the specified number off to a certain number of decimals and returns it as text, with optional commas, e.g., fixed(123.45678, 2) returns "123.46"
                            | "initials" ; text (Text); returns only the uppercase characters from within the given text, e.g., initials("John Smith") returns "JS"
                            | "insertkey" ; key (Text or Text Array), startDelimiter (Text), endDelimiter (Text); returns the provided text, wrapped with the specified delimiters, e.g., insertKey({"hello", "world"}, "[", "]") returns "[hello][world]"
                            | "insertkeyval" ; key (Text), value (Text), startDelimiter (Text), endDelimiter (Text); returns the provided key-value pairs, wrapped with the specified delimiters, e.g., insertkeyval({"hello","goodbye"}, {"alpha","beta"}, "[", "]") returns ""[hello=alpha][goodbye=beta]""
                            | "keyval" ; text (Text), keys (Text Array), separators (Text Array), delimiters (Text Array); returns the value(s) associated with the given key(s). This function performs the reverse of insertkeyval() function; e.g., keyval("hello=alpha][goodbye=beta]", {"hello"}, "=", "]") returns "alpha"
                            | "left" ; text (Text), numChars (Number); returns a specified number of characters from the text, starting from the first character; e.g., left("boston",3) returns "bos"
                            | "leftb" ; text (Text), numBytes (Number); returns a specified number of bytes from the text, starting from the first byte; e.g., leftb("boston",3) returns "bos"
                            | "len" ; text (Text); returns the length in characters of the text, e.g., len("boston") returns 6
                            | "lenb" ; text (Text); returns the length in bytes of the text, e.g., lenb("boston") returns 6
                            | "like" ; text (Text), withPattern (Text, where ? is any char, * is 0 or more chars, [chars] is any listed char. [^chars} is any BUT listed char, [number-number] given range ofnumbers); e.g., like("brian","*ian") returns true, e.g. pattern, "[0-2]4" matches "04" and "14" and "24", but not "74"
                            | "lower" ; text (Text); converts all characters in the text into lowercase (Unicode case folding), e.g., lower("BOSTON") returns "boston"
                            | "mid" ; text (Text), startNum (Number, 1-based), numChars (Number), e.g., mid("boston",4,2) returns "to"
                            | "midb" ; text (Text), startNum (Number, 1-based), numBytes (Number), e.g., midb("boston",4,2) returns "to"
                            | "padleft" ; text (Text), totalLength (Number); pads text with spaces on left to reach given totalLength, e.g., padleft("boston",10)  returns "    boston"
                            | "padright" ; text (Text), totalLength (Number); pads text with spaces on right to reach given totalLength, e.g., padright("boston",10)  returns "boston    "
                            | "proper" ; text (Text); converts each character in the text into proper case, meaning it will capitalize the first first letter of every word and convert the rest into lowercase, e.g., proper("coNvert eaCH cHaRacter iNTo ProPeR caSe") returns "Convert Each Character Into Proper Case"
                            | "replace" ; oldText (Text), startNum (Number, 1-based), numChars (Number), newText (Text); replaces a piece of the specified text with new text, e.g., replace("oldtext",1,3,"new") returns "newtext"
                            | "replaceb" ; oldText (Text), startNum (Number, 1-based), numBytes (Number), newText (Text); replaces a piece of the specified text with new text, e.g., replace("oldtext",1,3,"new") returns "newtext"
                            | "rept" ; text (Text), numberTimes (Number, the original text is not counted as a repetition); e.g., rept("do",3) returns "dododo"
                            | "right" ; text (Text), numChars (Number); returns a specified number of characters from the text, starting from the last character; e.g., right("boston",3) returns "ton"
                            | "rightb" ; text (Text), numBytes (Number); returns a specified number of bytes from the text, starting from the last byte; e.g., rightb("boston",3) returns "ton"
                            | "search" ; findText (Text), withinText (Text), startNum (Number, 1-based, optional); searches the text for the given, case insensitive substring. Returns the one-based positional index of the first character of the first match, zero if the substring is not found, e.g., search("to", "boston") returns 4
                            | "searchb" ; findText (Text), withinText (Text), startNum (Number, 1-based, optional); searches the text for the given, case insensitive substring. Returns the one-based positional index of the first byte of the first match, zero if the substring is not found, e.g., searchb("to", "boston") returns 4, searchb("tt", "café latte") returns 9 (as "é" character counts as 2 bytes)
                            | "soundex" ; text (Text); returns the soundex code, used to render similar sounding names via phonetic similarities into identical four (4) character codes; this helps to find the intended name when transcribing audio, e.g., soundex("John Smith") returns J525 as does soundex("John Smythe") and soundex("Johann Smythe"), but soundex("Brian Sullivan") and soundex("Bryan Sullivan") are both "B652"
                            | "split" ; text (Text), separator (Text); splits text into a list of text elements, delimited by the text specified in the separator, e.g., split("A sentence has words separated by spaces.", " ") returns {"A", "sentence", "has", "words", "separated", "by", "spaces."}
                            | "strip" ; text (Text); returns the provided text, minus any characters considered printable. Printable characters are the 95 printable ASCII characters plus three special characters: BACKSPACE (0x08), TAB (0x09), and NEWLINE (0x0a)
                            | "stripHtml" ; text (Text); changes the provided HTML string into a plain text string by converting <br>, <p>, and <div> to line breaks, stripping all other tags, and converting escaped characters into their display values, e.g., stripHtml("<p>Click <b>Save</b>.</p>") returns "Click Save."
                            | "stripwith" ; text (Text), charactersToStrip (Text); returns the provided text, minus any characters from charactersToStrip, e.g., stripwith("text string","xg t") returns "esrin"
                            | "substitute" ; baseTextToBeReturned (Text), textToReplace (Text), textToReplaceWith (Text); substitutes a specific part of a string with another string, e.g., substitute("hello world","hello","my") returns "my world"
                            | "text" ; number (Number), format (Text); allows you to format Number, Date, Time, or Date and time values as you convert them into text strings, see Text Format Guide; the returned text is internationalized where possible
                            | "toHtml" ; text (Text); escape reserved characters for HTNML, e.g., toHTML("Hello <br> World") returns "Hello &lt;br&gt; World"
                            | "trim" ; text (Text); removes all unnecessary spaces from the text. Only single spaces between words are considered necessary, e.g., trim(" this   text needs trimming ") returns "this text needs trimming"
                            | "upper" ; text (Text); converts all letters in the text into uppercase, e.g., upper("Boston") returns "BOSTON"
                            | "value" ; text (Text), format (Text); converts text representing a number into an actual number or datetime, e.g., value("12/13/2005","mm/dd/yyyy") yields a Date of December 13, 2005 or value("1,2,3",",") returns {1,2,3}

# Text Format Guide for Dates and Times
#
# Format | Output | Example | Returns
# mmmmm | J F M A M J J A S O N D | text(date(2020, 2, 27),"mmmmm") | F
# mmmm | January February March April May June July August September October November December | text(date(2020, 2, 27),"mmmm") | February
# mmm | Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec | text(date(2020, 2, 27),"mmm") | Feb
# mm | 01 .. 12 | text(date(2020, 2, 27),"mm") | 02
# m | 	1 .. 12 | text(date(2020, 2, 27),"m") | 2
# yyyy | four-digit year | text(date(2020, 2, 27),"yyyy") | 2020
# yy | two-digit year | text(date(2020, 2, 27),"yy") | 20
# ddd | 1st 2nd 3rd 4th 5th 6th 7th 8th 9th 10th 11th 12th 13th 14th 15th 16th 17th 18th 19th 20th 21st 22nd 23rd 24th 25th 26th 27th 28th 29th 30th 31st | text(date(2020, 5, 27),"ddd") | 27th
# dd | 01 .. 31 | text(date(2020, 2, 27),"dd") | 27
# d | 1 .. 31 | text(date(2020, 2, 27),"d") | 27
# hh | 01..12 (if AM/PM) or 00..23 (if no AM/PM) | text(datetime(2020, 2, 27,12,15,05),"hh") | 12
# h | 1..12 (if AM/PM) or 0..23 (if no AM/PM) | text(datetime(2020, 2, 27,12,15,05)),"h") | 12
# kk | hour 01..24 | text(datetime(2020, 2, 27,12,15,05),"kk") | 12
# k | hour 1..24 | text(datetime(2020, 2, 27,12,15,05),"k") | 12
# mm | minute 00..59 (If hour already processed, i.e., h to left anywhere in format) | text(datetime(2020, 2, 27, 12, 15, 05),"h:mm") | 12:15
# ss | second 00..59 | text(datetime(2020, 2, 27, 12, 15, 05),"ss") | 05
# AM/PM | AM/PM in uppercase | text(datetime(2020, 2, 27, 12, 15),"AM/PM") | PM
# am/pm | am/pm in lowercase | text(datetime(2020, 2, 27, 12, 15),"am/pm") | pm
# A/P | A/P in uppercase | text(datetime(2020, 2, 27, 12, 15),"A/P") | P
# a/p | a/p in lowercase | text(datetime(2020, 2, 27, 12, 15),"a/p") | p
# a | AM or PM in uppercase | text(datetime(2020, 2, 27, 12, 15),"a") | PM
# aa | AM or PM in uppercase | text(datetime(2020, 2, 27, 12, 15),"aa") | PM
# [h] | the number of hours in the era | text(datetime(2020, 2, 27, 12, 15, 05),"[h]") | -130116
# @ | serial date field | text(datetime(2020, 2, 27, 12, 15, 05),"@") | -5421.49
# dddd | Saturday, Sunday, Monday, Tuesday, Wednesday, Thursday, Friday | text(date(2020, 2, 27),"dddd") | Thursday
# EEEE | Saturday, Sunday, Monday, Tuesday, Wednesday, Thursday, Friday | text(date(2020, 2, 27),"EEEE") | Thursday
# z | Timezone Name short form | text(datetime(2020, 2, 27, 12, 15, 05),"z") | EST
# zzzz | Timezone Name long form | text(datetime(2020, 2, 27, 12, 15, 05),"zzzz") | Eastern Standard Time

# Text Format Guide for Numbers
# If the format you use contains the number sign (#) zero (0) or a question mark (?), then the output takes a number format. The output is then treated as a number rather than as a date/time.
# You can split the number format into positive;negative;zero;text formats (where each optional format is separated by a semi-colon [;]).
# Normally, positive numbers do not show a sign symbol. To use plus (+) or minus (-) symbols, specify the positive and negative number-formats separately (as in the following examples).
#  text(-3.434,"+0000.###;-0000.###")returns -0003.434
#  text(3.434,"+0000.###;-0000.###") returns +0003.434
#
# Table for LEFT of decimal point:
#
# Format | Output | Example | Returns
# 0 | Numeric digit or leading 0 | text(1234.5, "00000.00") | 01234.50
# # | Numeric digit or leading space | text(1234.5, "#####.##") | 1234.50
# , | Grouping seperator | text(1234.5, "##,###.##") | 1,234.50
# . | Decimal point. Switches to right of decimal formatting | text(1234.5, "#####.##") | 1234.50
# - | Always "-" | text(1234.5, "-#####.##") | -1234.50
# + | "+" if positive, "-" if negative | text(1234.5, "+#####.##") | +1234.50
# $ | The currency character | text(1234.5, "$####.##") | $1234.50
# % | Any % multiplies the number by 100 | text(0.50, "#%") | 50%
# (any other) | Any other given character | text(15, "#c") | 15c
#
# Table for RIGHT of decimal point:
#
# Format | Meaning
# 0 | Numeric digit or trailing 0
# # | Numeric digit or trailing space
# , | Grouping seperator
# $ | The currency character
# (any other) | Any other given character

text_function_keyword ::= "a!currency" ; value (Number), currency (Text, optional), decimals (Number, optional), locale (Text, optional)
                        | "a!formatPhoneNumber" ; phoneNumber (Text), countryCode (Text Array) , outputFormat (Text, one of "NATIONAL", "INTERNATIONAL", "E164" (the default), "RFC3966"); phone must be valid for given ISO countryCode array
                        | "a!isPhoneNumber" ; phoneNumber (Text), countryCode (Text Array) ; phone must be valid for given ISO countryCode array, e.g., a!isPhoneNumber(phoneNumber: "+52 55 5487 3100") returns true, a!isPhoneNumber(phoneNumber: "1-998-185-3133", "US") returns true
                        | "a!swissFranc" ; number (Number), decimals (Number, optional, default is 2), noApostrophes (Boolean default is false), showPrefixSymbol (Boolean default is false); e.g., a!swissFranc(number: 3213.43, showPrefixSymbol: 1) returns "CHF 3'213.43"

# Trigonometry functions - Mathematical trigonometric operations
trigonometry_function_positional ::= "acos" ; number (Number); arccosine in radians, e.g., acos(1) returns 0
                                    | "acosh" ; number (Number); hyperbolic arccosine in radians, e.g., acosh(2) returns 1.3169578969248165
                                    | "asin" ; number (Number); arcsine in radians, e.g., asin(1) returns 1.5707963267948965
                                    | "asinh" ; number (Number); hyperbolic arcsine in radians, e.g., asinh(2) returns 1.4436354751788103
                                    | "atan" ; number (Number); arctangent in radians, e.g., atan(1) returns 0.7853981633974483
                                    | "atanh" ; number (Number); hyperbolic arctangent in radians, e.g., atanh(.9) returns 1.4722194895832203
                                    | "cos" ; number (Number); cosine, e.g., cos(1) returns 0.5403023058681398
                                    | "cosh" ; number (Number); hyperbolic cosine, e.g., cosh(1) returns 1.5430806348152437
                                    | "degrees" ; radians (Number); converts radians to degrees, e.g., degrees(pi()) returns 180
                                    | "radians" ; degrees (Number); converts degrees to radians, e.g., radians(180) returns 3.141592653589793 (result of pi())
                                    | "sin" ; number (Number); sine, e.g., sin(1) returns 0.8414709848078965
                                    | "sinh" ; number (Number); hyperbolic sine, e.g., sinh(1) returns 1.1752011936438013
                                    | "tan" ; number (Number); tangent, e.g., tan(1) returns 1.5574077246549023
                                    | "tanh" ; number (Number); hyperbolic tangent, e.g., tanh(1) returns 0.7615941559557648

# Function arguments
argument_list ::= expression ("," expression)*

# Type constructors
# Type constructors may be used to construct CDTs (Complex DataTypes)
type_constructor ::= identifier "(" field_assignment_list? ")"
field_assignment_list ::= field_assignment ("," field_assignment)*
field_assignment ::= identifier ":" expression

# Arrays
# Note that array literals will automatically flatten
array ::= "{" array_elements? "}"
array_elements ::= expression ("," expression)*

# Maps
# Note that maps are always keyed by strings, but values may be of any type
map ::= "a!map" "(" map_fields? ")"
map_fields ::= map_field ("," map_field)*
map_field ::= identifier ":" expression

# Dictionaries
# Note that dictionaries are always keyed by strings, but values may be of any type; the values are wrapped in a Variant (Any Type)
dictionary ::= "{" dictionary_fields? "}"
dictionary_fields ::= dictionary_field ("," dictionary_field)*
dictionary_field ::= identifier ":" expression

# Index access (all indexes in SAIL are 1-based)
# Index access may be used for arrays, dictionaries or maps
index_access ::= primary_expression "[" expression "]"

# Field access
# Field access may also be done dynamically by using the index function
field_access ::= primary_expression "." identifier

# Comments may be included anywhere
block_comment ::= "/*" [^*]* "*/"

# Special tokens
elision ::= "_" ; if used as a parameter in a function call, then the function call is made into a new function call reference with this parameter missing, to be filled in upon call

# Basic character classes
digit ::= [0-9]
whitespace ::= [ \t\n\r]+

###
### User Interface Components and Data Follow
###

# Save context variables and restrictions
save_context ::= "save!value" ; ONLY valid within a!save's value parameter
# CRITICAL: save!value can ONLY be used inside the value parameter of a!save function
# WRONG: if(save!value, a!save(...), {})
# RIGHT: a!save(target: local!var, value: if(save!value, newValue, oldValue))

# Save operations
save_operation ::= a!save_function | save_into_list
save_into_list ::= "{" save_operation ("," save_operation)* "}"

# MARGIN AND SPACING VALUES TABLE
# Valid values for marginAbove, marginBelow, and spacing parameters:
# "NONE" - No margin/spacing
# "EVEN_LESS" - Minimal margin/spacing
# "LESS" - Reduced margin/spacing
# "STANDARD" - Default margin/spacing
# "MORE" - Increased margin/spacing
# "EVEN_MORE" - Maximum margin/spacing

# LABEL POSITION VALUES TABLE
# Valid values for labelPosition parameter in form components:
# "ABOVE" (default) - Label appears above the component
# "ADJACENT" - Label appears to the left of the component
# "COLLAPSED" - Label is hidden but still accessible to screen readers
# "JUSTIFIED" - Label aligns to the edge of the page alongside the component

# HEIGHT VALUES TABLE
# Valid values for height parameter in various components:
# "SHORT" - Compact height
# "SHORT_PLUS" - Slightly taller than short
# "MEDIUM" - Standard height
# "MEDIUM_PLUS" - Slightly taller than medium
# "TALL" - Large height
# "TALL_PLUS" - Slightly taller than tall
# "EXTRA_TALL" - Maximum height
# "AUTO" (default) - Height adjusts to content

# COLOR VALUES TABLE
# Valid color values for various color parameters:
# Predefined colors: "ACCENT", "POSITIVE", "WARN", "NEGATIVE", "SECONDARY", "STANDARD"
# Scheme colors: "CHARCOAL_SCHEME", "NAVY_SCHEME", "PLUM_SCHEME"
# Style colors: "SUCCESS", "INFO", "ERROR"
# Custom colors: Any valid hex color code (e.g., "#FF0000", "#00FF00")

# SIZE VALUES TABLE
# Valid values for size parameter in various components:
# "TINY" - Very small size
# "SMALL" - Small size
# "MEDIUM" - Standard size
# "LARGE" - Large size
# "EXTRA_SMALL" - Smaller than small (for headings)

# ALIGNMENT VALUES TABLE
# Valid values for align parameter:
# "LEFT" - Left alignment
# "CENTER" - Center alignment
# "RIGHT" - Right alignment

# BUTTON STYLE VALUES TABLE
# Valid values for style parameter in a!buttonWidget:
# "OUTLINE" (default) - Button with transparent background and colored border
# "GHOST" - Button with transparent background and colored border that switches to solid when highlighted
# "LINK" - Button with transparent background and border that switches to colored border when highlighted
# "SOLID" - Button with solid color background

# GRID BORDER STYLE VALUES TABLE
# Valid values for borderStyle parameter in grid components:
# "STANDARD" (default) - Standard border appearance
# "LIGHT" - Light border appearance

# SELECTION STYLE VALUES TABLE
# Valid values for selectionStyle parameter in grid components:
# "CHECKBOX" (default) - Selection using checkboxes
# "ROW_HIGHLIGHT" - Selection by highlighting entire rows

# CHOICE LAYOUT VALUES TABLE
# Valid values for choiceLayout parameter in choice components:
# "STACKED" - Choices arranged vertically
# "COMPACT" - Choices arranged horizontally when space allows

# SEARCH DISPLAY VALUES TABLE
# Valid values for searchDisplay parameter in dropdown components:
# "AUTO" - Search appears automatically based on number of choices
# "ON" - Search is always shown
# "OFF" - Search is never shown

# CARD SHAPE VALUES TABLE
# Valid values for shape parameter in a!cardLayout:
# "SQUARED" (default) - Square corners
# "SEMI_ROUNDED" - Slightly rounded corners
# "ROUNDED" - Fully rounded corners

# DECORATIVE BAR POSITION VALUES TABLE
# Valid values for decorativeBarPosition parameter in a!cardLayout:
# "TOP" - Bar at top of card
# "BOTTOM" - Bar at bottom of card
# "START" - Bar at start (left) of card
# "END" - Bar at end (right) of card
# "NONE" (default) - No decorative bar

# OVERLAY STYLE VALUES TABLE
# Valid values for style parameter in overlay components:
# "DARK" - Dark overlay
# "SEMI_DARK" - Semi-transparent dark overlay
# "LIGHT" - Light overlay
# "SEMI_LIGHT" - Semi-transparent light overlay

# COLUMN WIDTH VALUES TABLE
# Valid values for width parameter in column and grid configurations:
# "ICON" - Icon width (very narrow)
# "NARROW" - Narrow width
# "MEDIUM" - Medium width
# "WIDE" - Wide width
# "AUTO" - Automatic width based on content
# "DISTRIBUTE" - Distribute available space (for grid columns)
# "MINIMIZE" - Minimize width (for buttons)
# "FILL" - Fill available space (for buttons)

# STACK WHEN VALUES TABLE
# Valid values for stackWhen parameter in responsive layouts:
# "PHONE" - Stack on phone-sized screens
# "TABLET_PORTRAIT" - Stack on tablet portrait orientation
# "TABLET_LANDSCAPE" - Stack on tablet landscape orientation
# "DESKTOP_NARROW" - Stack on narrow desktop screens
# "DESKTOP" - Stack on standard desktop screens
# "DESKTOP_WIDE" - Stack on wide desktop screens

# Interface component functions
interface_component_function_keyword ::= action_component_keyword | browser_component_keyword | chart_component_keyword
                                       | display_component_keyword | grid_list_component_keyword | input_component_keyword
                                       | layout_component_keyword | picker_component_keyword | selection_component_keyword

# ACTION COMPONENTS - Components that trigger actions or navigation
action_component_keyword ::= "a!authorizationLink" ; text (Text), url (Text), openUrlIn (Text, optional)
                           | "a!buttonArrayLayout" ; buttons (Button Array), align (Text, optional), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional)
                           | "a!buttonLayout" ; primaryButtons (Button Array, optional), secondaryButtons (Button Array, optional), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional)
                           | "a!buttonWidget" ; label (Text), value (Any Type, optional), saveInto (Save Target, optional), submit (Boolean, optional), style (Text, optional; valid values: "OUTLINE" (default) button with transparent background and colored border, "GHOST" button with transparent background and colored border that switches to solid color when highlighted, "LINK" button with transparent background and border that switches to colored border when highlighted, "SOLID" button with solid color), color (Text, optional; valid values: "ACCENT" (default), "NEGATIVE", "SECONDARY", or any valid hex color), size (Text, optional; valid values: "SMALL", "STANDARD" (default), "LARGE"), disabled (Boolean, optional), marginAbove (Text, optional; valid values: "NONE" (default), "EVEN_LESS", "LESS", "STANDARD", "MORE", "EVEN_MORE"), marginBelow (Text, optional; valid values: "NONE" (default), "EVEN_LESS", "LESS", "STANDARD", "MORE", "EVEN_MORE"), showWhen (Boolean, optional), loadingIndicator (Boolean, optional), accessibilityText (Text, optional), tooltip (Text, optional), width (Text, optional; valid values: "MINIMIZE", "FILL"), icon (Text, optional; see Standard Icons list), iconPosition (Text, optional; valid values: "START" (default), "END"), confirmMessage (Text, optional), confirmHeader (Text, optional), confirmButtonLabel (Text, optional), cancelButtonLabel (Text, optional), validationGroup (Text, optional), validate (Boolean, optional), recaptchaSaveInto (List of saves, optional; for use in Portals only)
                           | "a!documentDownloadLink" ; document (DocumentId), text (Text, optional)
                           | "a!dynamicLink" ; label (Text), value (Any Type, optional), saveInto (Save Target, optional), showWhen (Boolean, optional), color (Text, optional), disabled (Boolean, optional)
                           | "a!linkField" ; links (Link Array), align (Text, optional), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                           | "a!newsEntryLink" ; newsEntry (News Entry), text (Text, optional)
                           | "a!processTaskLink" ; task (Number), text (Text, optional)
                           | "a!recordActionField" ; actions (RecordAction Array), style (Text, optional; valid values: "TOOLBAR", "LINKS", "CARDS", "SIDEBAR", "CALL_TO_ACTION", "MENU", "MENU_ICON"), align (Text, optional), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                           | "a!recordActionItem" ; action (Text), identifier (Any Type, optional), recordType (RecordType, optional), label (Text, optional), icon (Text, optional), style (Text, optional), color (Text, optional), disabled (Boolean, optional), tooltip (Text, optional), confirmHeader (Text, optional), confirmMessage (Text, optional), skipValidation (Boolean, optional), weight (Number, optional)
                           | "a!recordLink" ; recordType (RecordType), identifier (Any Type), text (Text, optional), openLinkIn (Text, optional), showWhen (Boolean, optional)
                           | "a!reportLink" ; report (Report), text (Text, optional), openUrlIn (Text, optional)
                           | "a!safeLink" ; uri (Text), text (Text, optional)
                           | "a!startProcessLink" ; processModel (ProcessModelId), processParameters (Any Type, optional), text (Text, optional)
                           | "a!submitLink" ; label (Text), value (Any Type, optional), saveInto (Save Target, optional), showWhen (Boolean, optional), skipValidation (Boolean, optional), confirmHeader (Text, optional), confirmMessage (Text, optional)
                           | "a!userRecordLink" ; user (User), text (Text, optional), openLinkIn (Text, optional), showWhen (Boolean, optional)

# BROWSER COMPONENTS - Components for browsing hierarchical data
browser_component_keyword ::= "a!documentAndFolderBrowserFieldColumns" ; showDocumentDetails (Boolean, optional), showFolderDetails (Boolean, optional)
                            | "a!documentBrowserFieldColumns" ; showDocumentDetails (Boolean, optional)
                            | "a!folderBrowserFieldColumns" ; showFolderDetails (Boolean, optional)
                            | "a!groupBrowserFieldColumns" ; showGroupDetails (Boolean, optional)
                            | "a!hierarchyBrowserFieldColumns" ; columns (HierarchyBrowserFieldColumn Array)
                            | "a!hierarchyBrowserFieldColumnsNode" ; primaryText (Text), secondaryText (Text, optional), details (Text Array, optional), image (Image, optional), link (Link, optional)
                            | "a!hierarchyBrowserFieldTree" ; children (HierarchyBrowserFieldTreeNode Array)
                            | "a!hierarchyBrowserFieldTreeNode" ; id (Text), parentId (Text, optional), label (Text), details (Text Array, optional), tooltip (Text, optional)
                            | "a!orgChartField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), rootNode (User), nodeConfigs (OrgChartNodeConfig Array, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!userAndGroupBrowserFieldColumns" ; showUserDetails (Boolean, optional), showGroupDetails (Boolean, optional)
                            | "a!userBrowserFieldColumns" ; showUserDetails (Boolean, optional)

# CHART COMPONENTS - Components for data visualization
chart_component_keyword ::= "a!areaChartConfig" ; primaryGrouping (Grouping), secondaryGrouping (Grouping, optional), measures (Measure Array), dataLimit (Number, optional), link (Link, optional), showTooltips (Boolean, optional), showDataLabels (Boolean, optional), allowDecimalAxisLabels (Boolean, optional), connectNulls (Boolean, optional), colorScheme (ColorScheme, optional), height (Text, optional; valid values: "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO"), xAxisTitle (Text, optional), yAxisTitle (Text, optional), yAxisMin (Number, optional), yAxisMax (Number, optional), referenceLines (ChartReferenceLine Array, optional)
                          | "a!areaChartField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), data (Any Type), config (AreaChartConfig), refreshAlways (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                          | "a!barChartConfig" ; primaryGrouping (Grouping), secondaryGrouping (Grouping, optional), measures (Measure Array), dataLimit (Number, optional), link (Link, optional), showTooltips (Boolean, optional), showDataLabels (Boolean, optional), allowDecimalAxisLabels (Boolean, optional), colorScheme (ColorScheme, optional), height (Text, optional; valid values: "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO"), xAxisTitle (Text, optional), yAxisTitle (Text, optional), yAxisMin (Number, optional), yAxisMax (Number, optional), stacking (Text, optional; valid values: "NONE", "NORMAL", "PERCENT"), referenceLines (ChartReferenceLine Array, optional)
                          | "a!barChartField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), data (Any Type), config (BarChartConfig), refreshAlways (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                          | "a!chartReferenceLine" ; label (Text), value (Number), color (Text, optional), style (Text, optional; valid values: "SOLID", "DASHED", "DOTTED")
                          | "a!chartSeries" ; label (Text), data (Number Array), color (Text, optional)
                          | "a!colorSchemeCustom" ; colors (Text Array)
                          | "a!columnChartConfig" ; primaryGrouping (Grouping), secondaryGrouping (Grouping, optional), measures (Measure Array), dataLimit (Number, optional), link (Link, optional), showTooltips (Boolean, optional), showDataLabels (Boolean, optional), allowDecimalAxisLabels (Boolean, optional), colorScheme (ColorScheme, optional), height (Text, optional; valid values: "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO"), xAxisTitle (Text, optional), yAxisTitle (Text, optional), yAxisMin (Number, optional), yAxisMax (Number, optional), stacking (Text, optional; valid values: "NONE", "NORMAL", "PERCENT"), referenceLines (ChartReferenceLine Array, optional)
                          | "a!columnChartField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), data (Any Type), config (ColumnChartConfig), refreshAlways (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                          | "a!grouping" ; field (Text), alias (Text, optional), sort (SortInfo Array, optional)
                          | "a!lineChartConfig" ; primaryGrouping (Grouping), secondaryGrouping (Grouping, optional), measures (Measure Array), dataLimit (Number, optional), link (Link, optional), showTooltips (Boolean, optional), showDataLabels (Boolean, optional), allowDecimalAxisLabels (Boolean, optional), connectNulls (Boolean, optional), colorScheme (ColorScheme, optional), height (Text, optional; valid values: "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO"), xAxisTitle (Text, optional), yAxisTitle (Text, optional), yAxisMin (Number, optional), yAxisMax (Number, optional), referenceLines (ChartReferenceLine Array, optional)
                          | "a!lineChartField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), data (Any Type), config (LineChartConfig), refreshAlways (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                          | "a!measure" ; field (Text), function (Text), alias (Text, optional), formatValue (Text, optional)
                          | "a!pieChartConfig" ; primaryGrouping (Grouping), measures (Measure Array), dataLimit (Number, optional), link (Link, optional), showTooltips (Boolean, optional), showDataLabels (Boolean, optional), showAsDonut (Boolean, optional), colorScheme (ColorScheme, optional), height (Text, optional; valid values: "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO")
                          | "a!pieChartField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), data (Any Type), config (PieChartConfig), refreshAlways (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                          | "a!scatterChartField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), categories (Text Array), series (ChartSeries Array), xAxisTitle (Text, optional), yAxisTitle (Text, optional), yAxisMin (Number, optional), yAxisMax (Number, optional), showLegend (Boolean, optional), allowDecimalAxisLabels (Boolean, optional), colorScheme (ColorScheme, optional), height (Text, optional; valid values: "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO"), refreshAlways (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)

# DISPLAY COMPONENTS - Components for displaying information
display_component_keyword ::= "a!documentImage" ; document (DocumentId), altText (Text, optional), caption (Text, optional), link (Link, optional), size (Text, optional; valid values: "ICON", "TINY", "SMALL", "MEDIUM", "LARGE", "FIT"), style (Text, optional; valid values: "STANDARD", "ROUNDED"), isThumbnail (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional)
                            | "a!documentViewerField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), document (DocumentId), height (Text, optional; valid values: "SHORT", "MEDIUM", "TALL", "AUTO"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!gaugeField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), percentage (Number, optional), primaryText (Text, optional), secondaryText (Text, optional), color (Text, optional; valid values: "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color), size (Text, optional; valid values: "SMALL", "MEDIUM", "LARGE"), align (Text, optional; valid values: "LEFT", "CENTER", "RIGHT"), tooltip (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!gaugeFraction" ; numerator (Number), denominator (Number), primaryText (Text, optional), secondaryText (Text, optional), color (Text, optional), size (Text, optional), align (Text, optional), tooltip (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!gaugeIcon" ; icon (Text), color (Text, optional), size (Text, optional), primaryText (Text, optional), secondaryText (Text, optional), align (Text, optional), tooltip (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!gaugePercentage" ; percentage (Number), primaryText (Text, optional), secondaryText (Text, optional), color (Text, optional), size (Text, optional), align (Text, optional), tooltip (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!headingField" ; text (Text), size (Text, optional; valid values: "LARGE", "MEDIUM", "SMALL", "EXTRA_SMALL"), color (Text, optional; valid values: "STANDARD", "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                            | "a!horizontalLine" ; thickness (Text, optional; valid values: "THIN", "MEDIUM", "THICK"), color (Text, optional; valid values: "STANDARD", "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional)
                            | "a!imageField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), images (Image Array), size (Text, optional; valid values: "ICON", "TINY", "SMALL", "MEDIUM", "LARGE", "FIT"), style (Text, optional; valid values: "STANDARD", "ROUNDED"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!kpiField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), value (Text), icon (Text, optional), color (Text, optional; valid values: "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color), size (Text, optional; valid values: "SMALL", "MEDIUM", "LARGE"), align (Text, optional; valid values: "LEFT", "CENTER", "RIGHT"), tooltip (Text, optional), refreshAlways (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!milestoneField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), steps (Text Array), active (Number, optional), complete (Number, optional), color (Text, optional; valid values: "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color), size (Text, optional; valid values: "SMALL", "MEDIUM", "LARGE"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!progressBarField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), percentage (Number), color (Text, optional; valid values: "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!richTextBulletedList" ; items (RichTextListItem Array)
                            | "a!richTextDisplayField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), value (RichTextItem Array), preventWrapping (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!richTextIcon" ; icon (Text), altText (Text, optional), caption (Text, optional), link (Link, optional), color (Text, optional), size (Text, optional; valid values: "SMALL", "MEDIUM", "LARGE")
                            | "a!richTextImage" ; image (Image), altText (Text, optional), caption (Text, optional), link (Link, optional), style (Text, optional)
                            | "a!richTextItem" ; text (Text), color (Text, optional), size (Text, optional; valid values: "SMALL", "MEDIUM", "LARGE"), style (Text, optional; valid values: "PLAIN", "EMPHASIS", "STRONG", "UNDERLINE", "STRIKE"), link (Link, optional)
                            | "a!richTextListItem" ; text (Text), color (Text, optional), size (Text, optional), style (Text, optional), nestedList (RichTextList, optional)
                            | "a!richTextNumberedList" ; items (RichTextListItem Array)
                            | "a!stampField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), icon (Text), text (Text), backgroundColor (Text, optional; valid values: "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color), contentColor (Text, optional; valid values: "STANDARD", "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color), size (Text, optional; valid values: "TINY", "SMALL", "MEDIUM", "LARGE"), align (Text, optional; valid values: "LEFT", "CENTER", "RIGHT"), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                            | "a!tagField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), tags (TagItem Array), size (Text, optional; valid values: "SMALL", "MEDIUM", "LARGE"), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                            | "a!tagItem" ; text (Text), backgroundColor (Text, optional; valid values: "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color), textColor (Text, optional; valid values: "STANDARD", "ACCENT", "POSITIVE", "WARN", "NEGATIVE", or any valid hex color)
                            | "a!timeDisplayField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), value (Number), unit (Text; valid values: "NANOSECONDS", "MICROSECONDS", "MILLISECONDS", "SECONDS", "MINUTES", "HOURS", "DAYS"), size (Text, optional; valid values: "SMALL", "MEDIUM", "LARGE"), refreshAlways (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!userImage" ; user (User), altText (Text, optional), caption (Text, optional), link (Link, optional), size (Text, optional; valid values: "ICON", "TINY", "SMALL", "MEDIUM", "LARGE"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional)
                            | "a!validationMessage" ; message (Text), validateAfter (Text, optional; valid values: "KEYPRESS", "UNFOCUS")
                            | "a!videoField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), source (Text), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!webContentField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), source (Text), altText (Text, optional), height (Text, optional; valid values: "SHORT", "MEDIUM", "TALL", "AUTO"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                            | "a!webImage" ; source (Text), altText (Text, optional), caption (Text, optional), link (Link, optional), size (Text, optional; valid values: "ICON", "TINY", "SMALL", "MEDIUM", "LARGE", "FIT"), style (Text, optional; valid values: "STANDARD", "ROUNDED"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional)
                            | "a!webVideo" ; source (Text), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)

# GRID AND LIST COMPONENTS - Components for displaying data in tabular or list format
grid_list_component_keyword ::= "a!eventData" ; dataType (Text), dataValue (Any Type)
                              | "a!eventHistoryListField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), data (Any Type), config (EventHistoryListConfig), refreshAlways (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                              | "a!gridColumn" ; label (Text, optional), field (Text, optional), data (Any Type, optional), links (Link Array, optional), sortField (Text, optional), align (Text, optional; valid values: "LEFT", "CENTER", "RIGHT"), width (Text, optional; valid values: "ICON", "NARROW", "MEDIUM", "WIDE", "AUTO"), showWhen (Boolean, optional)
                              | "a!gridField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), data (Any Type), columns (GridColumn Array), pageSize (Number, optional), initialSorts (SortInfo Array, optional), pagingSaveInto (Save Target, optional), selectable (Boolean, optional), selectionSaveInto (Save Target, optional), selectionStyle (Text, optional; valid values: "CHECKBOX" (default), "ROW_HIGHLIGHT"), selectionRequired (Boolean, optional), selectionRequiredMessage (Text, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), height (Text, optional; valid values: "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO"), borderStyle (Text, optional; valid values: "STANDARD" (default), "LIGHT"), shadeAlternateRows (Boolean, optional), rowHeader (Text, optional), accessibilityText (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional) ; provides fv!index, fv!item, fv!isSelected, fv!selectedItems
                              | "a!gridLayout" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), headerCells (GridLayoutHeaderCell Array), columnConfigs (GridLayoutColumnConfig Array, optional), rows (GridRowLayout Array), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional), selectable (Boolean, optional; default false), selectionDisabled (Boolean, optional; default false), selectionRequired (Boolean, optional; default false), selectionValue (List of Variant, optional), selectionSaveInto (List of Save, optional), addRowLink (Any Type, optional), totalCount (Number, optional), emptyGridMessage (Text, optional), shadeAlternateRows (Boolean, optional; default true), spacing (Text, optional; valid values: "STANDARD" (web default), "DENSE" (mobile default)), height (Text, optional; valid values: "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO" (default)), borderStyle (Text, optional; valid values: "STANDARD" (default), "LIGHT"), selectionStyle (Text, optional; valid values: "CHECKBOX" (default), "ROW_HIGHLIGHT"), rowHeader (Number, optional), allowRowReordering (Boolean, optional; default false), rowOrderTooltip (Boolean, optional; default true), rowOrderData (Any Type, optional), rowOrderField (Any Type, optional)
                              | "a!gridLayoutColumnConfig" ; width (Text; valid values: "ICON", "NARROW", "MEDIUM", "WIDE", "AUTO", "DISTRIBUTE"), weight (Number, optional), showWhen (Boolean, optional)
                              | "a!gridLayoutHeaderCell" ; label (Text), align (Text, optional; valid values: "LEFT", "CENTER", "RIGHT")
                              | "a!gridRowLayout" ; contents (Any Type Array), id (Number, optional)

# INPUT COMPONENTS - Components for user input
input_component_keyword ::= "a!barcodeField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), value (Text), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                          | "a!dataFabricChatField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), chatbotId (Text), height (Text, optional; valid values: "SHORT", "MEDIUM", "TALL", "AUTO"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                          | "a!dateField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), value (Date), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                          | "a!dateTimeField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), value (DateTime), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                          | "a!documentsChatField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), folders (Folder Array), height (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                          | "a!encryptedTextField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), value (Encrypted Text), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                          | "a!fileUploadField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), target (FolderId), value (Document Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), maxSelections (Number, optional), buttonStyle (Text, optional; valid values: "NORMAL", "OUTLINE"), fileNames (Text Array, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value, fv!files
                          | "a!floatingPointField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), value (Decimal), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                          | "a!integerField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), value (Number), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                          | "a!paragraphField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), value (Text), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), height (Text, optional; valid values: "SHORT", "MEDIUM", "TALL", "AUTO"), placeholder (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), characterLimit (Number, optional), showCharacterCount (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                          | "a!recordsChatField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), recordType (RecordType), height (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                          | "a!signatureField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), value (Text), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                          | "a!styledTextEditorField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), value (Styled Text), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), height (Text, optional; valid values: "SHORT", "MEDIUM", "TALL", "AUTO"), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                          | "a!textField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), value (Text), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), placeholder (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), characterLimit (Number, optional), showCharacterCount (Boolean, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value

# LAYOUT COMPONENTS - Components for organizing and structuring interfaces
layout_component_keyword ::= "a!barOverlay" ; position (Text; valid values: "TOP", "BOTTOM"), contents (Any Type Array), style (Text, optional; valid values: "DARK", "SEMI_DARK", "LIGHT", "SEMI_LIGHT"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional)
                           | "a!billboardLayout" ; backgroundMedia (Image, optional), backgroundColor (Text, optional; valid values: any valid hex color or "TRANSPARENT"), backgroundColorOpacity (Text, optional; valid values: "LOW", "MEDIUM", "HIGH"), height (Text, optional; valid values: "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO"), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), contents (Any Type Array), accessibilityText (Text, optional)
                           | "a!boxLayout" ; label (Text, optional), contents (Any Type Array), style (Text, optional; valid values: "STANDARD", "ACCENT", "SUCCESS", "INFO", "WARN", "ERROR"), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                           | "a!cardGroupLayout" ; cards (CardLayout Array), height (Text, optional; valid values: "EXTRA_SHORT", "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO"), style (Text, optional), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                           | "a!cardLayout" ; contents (Any Type Array), link (Link, optional), height (Text, optional; valid values: "EXTRA_SHORT", "SHORT", "SHORT_PLUS", "MEDIUM", "MEDIUM_PLUS", "TALL", "TALL_PLUS", "EXTRA_TALL", "AUTO" (default)), style (Text, optional; valid values: any valid hex color or "NONE" (default), "TRANSPARENT", "STANDARD", "ACCENT", "SUCCESS", "INFO", "WARN", "ERROR", "CHARCOAL_SCHEME", "NAVY_SCHEME", "PLUM_SCHEME"), showBorder (Boolean, optional; default true), showShadow (Boolean, optional; default false), tooltip (Text, optional), padding (Text, optional; valid values: "NONE", "EVEN_LESS", "LESS" (default), "STANDARD", "MORE", "EVEN_MORE"), marginAbove (Text, optional; valid values: "NONE" (default), "EVEN_LESS", "LESS", "STANDARD", "MORE", "EVEN_MORE"), marginBelow (Text, optional; valid values: "NONE" (default), "EVEN_LESS", "LESS", "STANDARD", "MORE", "EVEN_MORE"), showWhen (Boolean, optional), accessibilityText (Text, optional), shape (Text, optional; valid values: "SQUARED" (default), "SEMI_ROUNDED", "ROUNDED"), decorativeBarPosition (Text, optional; valid values: "TOP", "BOTTOM", "START", "END", "NONE" (default)), decorativeBarColor (Text, optional; valid values: any valid hex color or "ACCENT" (default), "POSITIVE", "WARN", "NEGATIVE"), borderColor (Text, optional; valid values: any valid hex color or "STANDARD" (default), "ACCENT", "POSITIVE", "WARN", "NEGATIVE")
                           | "a!columnLayout" ; contents (Any Type Array), width (Text, optional; valid values: "NARROW", "MEDIUM", "WIDE", "AUTO")
                           | "a!columnOverlay" ; position (Text; valid values: "START", "CENTER", "END"), contents (Any Type Array), width (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional)
                           | "a!columnsLayout" ; columns (ColumnLayout Array), alignVertical (Text, optional; valid values: "TOP", "MIDDLE", "BOTTOM"), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), stackWhen (Text Array, optional; valid values: "PHONE", "TABLET_PORTRAIT", "TABLET_LANDSCAPE", "DESKTOP_NARROW", "DESKTOP", "DESKTOP_WIDE"), accessibilityText (Text, optional)
                           | "a!formLayout" ; label (Text, optional), instructions (Text, optional), contents (Any Type Array), buttons (Button Array, optional), validations (Text Array, optional), validationGroup (Text, optional), skipValidation (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                           | "a!fullOverlay" ; contents (Any Type Array), style (Text, optional; valid values: "DARK", "SEMI_DARK", "LIGHT", "SEMI_LIGHT"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional)
                           | "a!headerContentLayout" ; header (Any Type Array), contents (Any Type Array), backgroundColor (Text, optional; valid values: "White" (default), "Transparent", "Charcoal Scheme", "Navy Scheme", "Plum Scheme", or any valid hex color), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                           | "a!pane" ; contents (Any Type Array)
                           | "a!paneLayout" ; firstPane (Pane), secondPane (Pane), dividerPosition (Number, optional), dividerStyle (Text, optional; valid values: "STANDARD", "THICK"), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional)
                           | "a!sectionLayout" ; label (Text, optional), contents (Any Type Array), isCollapsible (Boolean, optional), isInitiallyCollapsed (Boolean, optional), divider (Text, optional; valid values: "NONE", "ABOVE", "BELOW"), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), accessibilityText (Text, optional)
                           | "a!sideBySideItem" ; item (Any Type), width (Text, optional; valid values: "MINIMIZE", "1X", "2X", "3X", "4X", "5X", "6X", "7X", "8X", "9X", "10X", "AUTO"), showWhen (Boolean, optional)
                           | "a!sideBySideLayout" ; items (SideBySideItem Array), alignVertical (Text, optional; valid values: "TOP", "MIDDLE", "BOTTOM"), spacing (Text, optional; valid values: "NONE", "SPARSE", "STANDARD", "DENSE"), marginAbove (Text, optional), marginBelow (Text, optional), showWhen (Boolean, optional), stackWhen (Text Array, optional; valid values: "PHONE", "TABLET_PORTRAIT", "TABLET_LANDSCAPE", "DESKTOP_NARROW", "DESKTOP", "DESKTOP_WIDE"), accessibilityText (Text, optional)

# PICKER COMPONENTS - Components for selecting from predefined lists
picker_component_keyword ::= "a!pickerFieldCustom" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), maxSelections (Number, optional), suggestFunction (Any Type), selectedLabels (Text Array), value (Any Type Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                               | "a!pickerFieldDocuments" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), maxSelections (Number, optional), value (Document Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), folderFilter (Folder, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                               | "a!pickerFieldDocumentsAndFolders" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), maxSelections (Number, optional), value (Any Type Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), folderFilter (Folder, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                               | "a!pickerFieldFolders" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), maxSelections (Number, optional), value (Folder Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), folderFilter (Folder, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                               | "a!pickerFieldGroups" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), maxSelections (Number, optional), value (Group Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), groupFilter (Group, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                               | "a!pickerFieldRecords" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), maxSelections (Number, optional), recordType (RecordType), filters (Any Type Array, optional), value (Any Type Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                               | "a!pickerFieldUsers" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), maxSelections (Number, optional), value (User Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), groupFilter (Group, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                               | "a!pickerFieldUsersAndGroups" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), maxSelections (Number, optional), value (Any Type Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), readOnly (Boolean, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), groupFilter (Group, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value

# SELECTION COMPONENTS - Components for selecting from choices
selection_component_keyword ::= "a!cardChoiceField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), data (Any Type), sort (SortInfo Array, optional), cardTemplate (CardTemplate), value (Any Type Array), saveInto (Save Target, optional), maxSelections (Number, optional), required (Boolean, optional), requiredMessage (Text, optional), disabled (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), accessibilityText (Text, optional) ; provides save!value, fv!index, fv!item, fv!isSelected
                                  | "a!cardTemplateBarTextJustified" ; id (Any Type), primaryText (Text), secondaryText (Text, optional), details (Text Array, optional), icon (Text, optional), iconColor (Text, optional), iconAltText (Text, optional), tooltip (Text, optional)
                                  | "a!cardTemplateBarTextStacked" ; id (Any Type), primaryText (Text), secondaryText (Text, optional), details (Text Array, optional), icon (Text, optional), iconColor (Text, optional), iconAltText (Text, optional), tooltip (Text, optional)
                                  | "a!cardTemplateTile" ; id (Any Type), primaryText (Text), secondaryText (Text, optional), details (Text Array, optional), image (Image, optional), icon (Text, optional), iconColor (Text, optional), iconAltText (Text, optional), tooltip (Text, optional)
                                  | "a!checkboxField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), choiceLabels (Text Array), choiceValues (Any Type Array), value (Any Type Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), disabled (Boolean, optional), choiceLayout (Text, optional; valid values: "STACKED", "COMPACT"), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                                  | "a!checkboxFieldByIndex" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), choiceLabels (Text Array), value (Number Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), disabled (Boolean, optional), choiceLayout (Text, optional; valid values: "STACKED", "COMPACT"), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                                  | "a!dropdownField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), choiceLabels (Text Array), choiceValues (Any Type Array), value (Any Type), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), searchDisplay (Text, optional; valid values: "AUTO", "ON", "OFF"), accessibilityText (Text, optional) ; provides save!value
                                  | "a!dropdownFieldByIndex" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), choiceLabels (Text Array), value (Number), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), searchDisplay (Text, optional; valid values: "AUTO", "ON", "OFF"), accessibilityText (Text, optional) ; provides save!value
                                  | "a!multipleDropdownField" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), choiceLabels (Text Array), choiceValues (Any Type Array), value (Any Type Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), searchDisplay (Text, optional; valid values: "AUTO", "ON", "OFF"), accessibilityText (Text, optional) ; provides save!value
                                  | "a!multipleDropdownFieldByIndex" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), placeholder (Text, optional), choiceLabels (Text Array), value (Number Array), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), disabled (Boolean, optional), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), searchDisplay (Text, optional; valid values: "AUTO", "ON", "OFF"), accessibilityText (Text, optional) ; provides save!value
                                  | "a!radioButtonField" ; label (Text, optional), labelPosition (Text, optional; valid values: "ABOVE" (default), "ADJACENT", "COLLAPSED", "JUSTIFIED"), instructions (Text, optional), helpTooltip (Text, optional), choiceLabels (Text Array), choiceValues (Any Type Array), value (Any Type), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), disabled (Boolean, optional), choiceLayout (Text, optional; valid values: "STACKED", "COMPACT"), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value
                                  | "a!radioButtonFieldByIndex" ; label (Text, optional), labelPosition (Text, optional), instructions (Text, optional), helpTooltip (Text, optional), choiceLabels (Text Array), value (Number), saveInto (Save Target, optional), required (Boolean, optional), requiredMessage (Text, optional), disabled (Boolean, optional), choiceLayout (Text, optional; valid values: "STACKED", "COMPACT"), validations (Text Array, optional), validationGroup (Text, optional), refreshAlways (Boolean, optional), refreshAfter (Any Type Array, optional), refreshOnReferencedVarChange (Boolean, optional), refreshOnVarChange (Any Type Array, optional), refreshInterval (Number, optional), showWhen (Boolean, optional), marginAbove (Text, optional), marginBelow (Text, optional), accessibilityText (Text, optional) ; provides save!value

###
### REACTIONS are only usable in a saveInto claude
### (NOT YET REVIEWED)
###

# Smart service functions can only be used in saveInto parameters
smart_service_function_keyword ::= communication_service_keyword | data_service_keyword | document_generation_service_keyword
                                 | document_management_service_keyword | identity_management_service_keyword
                                 | process_management_service_keyword | testing_service_keyword

communication_service_keyword ::= "a!sendPushNotification" ; users (User Array), title (Text), message (Text), badgeNumber (Number, optional), sound (Text, optional), data (Map, optional)

data_service_keyword ::= "a!deleteFromDataStoreEntities" ; dataStoreEntity (Data Store Entity), identifiers (Any Type Array)
                        | "a!deleteRecords" ; records (RecordIdentifier Array), onSuccess (Any Type, optional), onError (Any Type, optional)
                        | "a!executeStoredProcedureOnSave" ; dataSource (Text), procedureName (Text), inputs (StoredProcedureInput Array, optional), timeout (Number, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                        | "a!syncRecords" ; recordType (RecordType), records (Map Array), onSuccess (Any Type, optional), onError (Any Type, optional)
                        | "a!writeRecords" ; records (Map Array), onSuccess (Any Type, optional), onError (Any Type, optional)
                        | "a!writeToDataStoreEntity" ; dataStoreEntity (Data Store Entity), valueToStore (Map), onSuccess (Any Type, optional), onError (Any Type, optional)
                        | "a!writeToMultipleDataStoreEntities" ; dataStoreEntities (Map Array), onSuccess (Any Type, optional), onError (Any Type, optional)

document_generation_service_keyword ::= "a!exportDataStoreEntityToCsv" ; entity (Data Store Entity), documentName (Text), documentDescription (Text, optional), saveInFolder (FolderId), customFieldLabels (Map, optional), filters (QueryFilter Array, optional), sortInfo (SortInfo Array, optional), selection (QuerySelection, optional), pagingInfo (PagingInfo, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                       | "a!exportDataStoreEntityToExcel" ; entity (Data Store Entity), documentName (Text), documentDescription (Text, optional), saveInFolder (FolderId), customFieldLabels (Map, optional), filters (QueryFilter Array, optional), sortInfo (SortInfo Array, optional), selection (QuerySelection, optional), pagingInfo (PagingInfo, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                       | "a!exportProcessReportToCsv" ; report (Report), documentName (Text), documentDescription (Text, optional), saveInFolder (FolderId), onSuccess (Any Type, optional), onError (Any Type, optional)
                                       | "a!exportProcessReportToExcel" ; report (Report), documentName (Text), documentDescription (Text, optional), saveInFolder (FolderId), onSuccess (Any Type, optional), onError (Any Type, optional)

document_management_service_keyword ::= "a!createFolder" ; name (Text), description (Text, optional), parent (FolderId), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!createKnowledgeCenter" ; name (Text), description (Text, optional), parent (KnowledgeCenterId, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!deleteDocument" ; document (DocumentId), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!deleteFolder" ; folder (FolderId), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!deleteKnowledgeCenter" ; knowledgeCenter (KnowledgeCenterId), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!editDocumentProperties" ; document (DocumentId), name (Text, optional), description (Text, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!editFolderProperties" ; folder (FolderId), name (Text, optional), description (Text, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!editKnowledgeCenterProperties" ; knowledgeCenter (KnowledgeCenterId), name (Text, optional), description (Text, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!lockDocument" ; document (DocumentId), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!modifyFolderSecurity" ; folder (FolderId), readers (User or Group Array, optional), authors (User or Group Array, optional), administrators (User or Group Array, optional), denyReaders (User or Group Array, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!modifyKnowledgeCenterSecurity" ; knowledgeCenter (KnowledgeCenterId), readers (User or Group Array, optional), authors (User or Group Array, optional), administrators (User or Group Array, optional), denyReaders (User or Group Array, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!moveDocument" ; document (DocumentId), folder (FolderId), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!moveFolder" ; folder (FolderId), parent (FolderId), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!unlockDocument" ; document (DocumentId), onSuccess (Any Type, optional), onError (Any Type, optional)

identity_management_service_keyword ::= "a!addAdminsToGroup" ; group (GroupId), newAdmins (User or Group Array), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!addMembersToGroup" ; group (GroupId), newMembers (User or Group Array), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!createGroup" ; name (Text), description (Text, optional), parentGroup (Group, optional), securityType (Text, optional), groupType (Text, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!createUser" ; username (Text), firstName (Text), lastName (Text), emailAddress (Text), userType (Text, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!deactivateUser" ; user (User), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!deleteGroup" ; group (GroupId), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!editGroup" ; group (GroupId), name (Text, optional), description (Text, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!modifyUserSecurity" ; user (User), administrators (User or Group Array, optional), viewers (User or Group Array, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!reactivateUser" ; user (User), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!removeGroupAdmins" ; group (GroupId), adminsToRemove (User or Group Array), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!removeGroupMembers" ; group (GroupId), membersToRemove (User or Group Array), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!renameUsers" ; users (User Array), newUsernames (Text Array), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!setGroupAttributes" ; group (GroupId), attributes (Map), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!updateUserProfile" ; user (User), firstName (Text, optional), lastName (Text, optional), displayName (Text, optional), emailAddress (Text, optional), officePhone (Text, optional), mobilePhone (Text, optional), homePhone (Text, optional), address1 (Text, optional), address2 (Text, optional), address3 (Text, optional), city (Text, optional), state (Text, optional), province (Text, optional), zipCode (Text, optional), country (Text, optional), locale (Text, optional), timeZone (Text, optional), calendar (Text, optional), customFields (Map, optional), onSuccess (Any Type, optional), onError (Any Type, optional)
                                      | "a!updateUserType" ; user (User), userType (Text), onSuccess (Any Type, optional), onError (Any Type, optional)

process_management_service_keyword ::= "a!cancelProcess" ; processId (Number), onSuccess (Any Type, optional), onError (Any Type, optional)
                                     | "a!completeTask" ; taskId (Number), onSuccess (Any Type, optional), onError (Any Type, optional)
                                     | "a!startProcess" ; processModel (ProcessModelId), processParameters (Map, optional), onSuccess (Any Type, optional), onError (Any Type, optional)

testing_service_keyword ::= "a!startRuleTestsAll" ; onSuccess (Any Type, optional), onError (Any Type, optional)
                           | "a!startRuleTestsApplications" ; applications (Application Array), onSuccess (Any Type, optional), onError (Any Type, optional)
                           | "a!testRunResultForId" ; testRunId (Number)
                           | "a!testRunStatusForId" ; testRunId (Number)
