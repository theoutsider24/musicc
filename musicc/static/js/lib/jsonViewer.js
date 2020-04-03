/**
 * Taken from https://www.jqueryscript.net/other/json-to-table-jsonviewer.html 
 * 
 * ***Project JSON Table Viewer***
 * 
 * A jQuery based plugin to display Javascript Objects/Arrays into a table based structure.
 * 
 * **Sample Usage:** [HTML]
 * 
 * <pre id='jsonView'></pre>
 * <script src="./path/to/jsonViewer.js"></script>
 * <script>
 *  var options={bootstrap:true,tableBordered:true}; //The options for conversion, check below for list of all options.
 *  var jsonObject={name:"Aniruddha Sarkar",country:"India"}; //The object to be converted into table.
 *  $('#jsonView').jsonTable(jsonObject,options); //Displaying the JS Object/Array
 * </script>
 * 
 * **Options:**
 * 1. bootstrap     : Whether to use the bootstrap classes or not. Default=true.
 * 2. arrayIndex    : Whether to view the indices of array elements. Default=false.
 * 3. tableBordered : Whether to use borders in table. Requires bootstrap to be enabled. Default=false.
 * 4. objectClass   : The class which to be used for coloring objects. Requires bootstrap to be enabled. Default="warning".
 * 5. arrayClass    : The class which to be used for coloring array. Requires bootstrap to be enabled. Default="info".
 * 6. valueClass    : The class which to be used for coloring primitive values. Requires bootstrap to be enabled. Default="success".
 * 7. nullClass     : The class which to be used for coloring null values. Requires bootstrap to be enabled. Default="danger".
 */

(function($){
    $.fn.jsonTable=function(__data,options={}){
        /** Checks if bootstrap is selected and available, or if bootstrap is unselected. */
        if( ! options.bootstrap || ( options.bootstrap && typeof $().modal == 'function')){

            /** Initialising default values if not set. */
            if(!options.hasOwnProperty('bootstrap'))options.bootstrap=true;
            if(!options.hasOwnProperty('arrayIndex'))options.arrayIndex=false;
            if(options.bootstrap){
                if(!options.hasOwnProperty('tableBordered'))options.tableBordered=false;
                if(!options.objectClass)options.objectClass="warning";
                if(!options.arrayClass)options.arrayClass="info";
                if(!options.nullClass)options.nullClass="danger";
                if(!options.valueClass)options.valueClass="success";
            }

            
            /** Checks if the data provided is an array. */
            if(Array.isArray(__data)){
                this.html(parseArray(__data,options));
            }
            
            /** Checks if the data provided is an object. */
            else if(__data instanceof Object){
                this.html(parseObject(__data,options));
            }
            
            /** Checks if the data provided is a primitive type. */
            else if(__data){
                this.html(__data);
            }
            
            /** Checks if the data provided is null. */
            else {
                this.html("");
            }
        }
        else{
            this.html("<div "+(options.bootstrap?"class='danger'":"")+">Bootstrap needs to be loaded before this plugin is loaded!</div>");
        }
    }
}(jQuery));

/**
 * Generates HTML table based on the __array parameter, using the options provided.
 * @param {*} __array The JS array which is to be converted to HTML.
 * @param {*} options The JS Object containing optional parameters for the conversion.
 * @returns String containing the HTML Output.
 */
function parseArray(__array,options){
    var data1="";
    var data2="";
    for (const __key in __array) {
        var __value=__array[__key];
        if(Array.isArray(__value)){
            data1+="<th "+(options.bootstrap?"class='"+(options.arrayClass)+"'":"")+">"+__key+"</th>";
            data2+="<tr><td "+(options.bootstrap?"class='"+(options.arrayClass)+"'":"")+">"+parseArray(__value,options)+"</td></tr>";
        }
        else if(__value instanceof Object){
            data1+="<th "+(options.bootstrap?"class='"+(options.objectClass)+"'":"")+">"+__key+"</th>";
            data2+="<tr><td "+(options.bootstrap?"class='"+(options.objectClass)+"'":"")+">"+parseObject(__value,options)+"</td></tr>";
        }
        else if(__value){
            data1+="<th "+(options.bootstrap?"class='"+(options.valueClass)+"'":"")+">"+__key+"</th>";
            data2+="<tr><td "+(options.bootstrap?"class='"+(options.valueClass)+"'":"")+">"+__value+"</td></tr>";
        }
        else{
            data1+="<th "+(options.bootstrap?"class='"+(options.nullClass)+"'":"")+">"+__key+"</th>";
            data2+="<tr><td "+(options.bootstrap?"class='"+(options.nullClass)+"'":"")+">"+__value+"</td></tr>";
        }
    }
    return "<table "+(options.bootstrap?"class='table table-bordered "+(options.arrayClass)+"'":"")+">"+(options.arrayIndex?"<thead>"+data1+"</thead>":"")+"<tbody><tr>"+data2+"</tr></tbody></table>";
}

/**
 * Generates HTML table based on the __array parameter, using the options provided.
 * @param {*} __object The JS array which is to be converted to HTML.
 * @param {*} options The JS Object containing optional parameters for the conversion.
 * @returns String containing the HTML Output.
 */
function parseObject(__object,options){
    var data="<table "+(options.bootstrap?"class='table "+(options.tableBordered?"table-bordered":"")+" "+(options.objectClass)+"'":"")+">";
    for (const __key in __object) {
        var __value=__object[__key];
        if(Array.isArray(__value)){
            data+="<tr "+(options.bootstrap?"class='"+(options.arrayClass)+"'":"")+"><td>"+__key+"</td><td "+(options.bootstrap?"class='"+(options.arrayClass)+"'":"")+">"+parseArray(__value,options)+"</td></tr>";
        }
        else if(__value instanceof Object){
            data+="<tr "+(options.bootstrap?"class='"+(options.objectClass)+"'":"")+"><td>"+__key+"</td><td "+(options.bootstrap?"class='"+(options.objectClass)+"'":"")+">"+parseObject(__value,options)+"</td></tr>";
        }
        else if(__value){
            data+="<tr "+(options.bootstrap?"class='"+(options.valueClass)+"'":"")+"><td>"+(__key !== "@value" ? __key : "") +"</td><td "+(options.bootstrap?"class='"+(options.valueClass)+"'":"")+">"+__value+"</td></tr>";
        }
        else{
            data+="<tr "+(options.bootstrap?"class='"+(options.nullClass)+"'":"")+"><td>"+__key+"</td><td "+(options.bootstrap?"class='"+(options.nullClass)+"'":"")+">"+__value+"</td></tr>";
        }
    }
    return data+"</table>";
}
