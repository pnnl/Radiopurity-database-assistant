var fields = {"isotope": 2, "value": 4, "units": 5, "symerr_conf": 7, "sym_err_units": 8, "asymerr": 10};
//The above corresponds to which values are in which columns in the tables storing the measurement results as displayed on the search HTML pages
var curr_values = {};

document.getElementById("units_convert_button").onclick= function(){
	loading_icon = document.getElementById("loading_icon");
	loading_icon.setAttribute("src", "./static/logos/loading_gif.jpg");
	console.log("Added the loading icon");
}

document.getElementById("units_convert_button").onclick= function(){
	//This is done when the "Convert" button next to the dropdown menu selecting the units is pressed
	add_loading_icon();
	unit_conversions();
	remove_loading_icon();
}

function unit_conversions(){
	var dropdown_units = document.getElementById("units_list");
	var chosen_unit = dropdown_units.options[dropdown_units.selectedIndex].text;
	console.log("Chosen units: " + chosen_unit);
	tables = document.getElementsByClassName("measurement-results-table"); //This is extracting all of the tables of measurement results in the extended view
	banners = document.getElementsByClassName("collapsible");//This is extracing the measurement values in the banner (button to show extended view)
	if(tables.length != banners.length){console.log("We may have a problem");}//Shouldn't happen, but would need to know
	for(var i = 0;i < tables.length;i++){
		table = tables[i];
		banner = banners[i];
		banner_val = (banner.getElementsByClassName("collapsiblebutton-vals")[0].getElementsByTagName("span"));//Each value is within a <span></span> block
		for(var j=0, row;row = table.rows[j];j++){
			for(var field in fields){
				if(empty_element_check(row.cells[fields[field]])){
					//Will cause an Error if the value is empty
					curr_values[field] = row.cells[fields[field]].getElementsByTagName("p")[0].innerHTML;//curr_values holds what is currently displayed
				}
				else{
					curr_values[field] = "";
				}
			}
			var units_and_value_changed = 0;
			results = unit_conversion_main(curr_values["units"], chosen_unit, parseFloat(curr_values["value"]), curr_values["isotope"]);
			
			if(parseFloat(curr_values["value"]) != 0.0) //This is to prevent a division by 0
				var conversion_ratio = results.value/parseFloat(curr_values["value"]);//This represents by which the absolute errors will be scaled as well
			else
				conversion_ratio = 1; //This would keep the value at 0
			
			//This above calls the main function for converting the units, where results.value is the altered value, and results.units is the new unit
			if(curr_values["values"] != "") {
				results.value = round_values(curr_values["value"], results.value);
				//This above rounds the converted value that will be displayed to the same precision as the original value
				row.cells[4].getElementsByTagName("p")[0].innerHTML = results.value;
				//4 comes from the fact that the value is in column indexed 4 in the results table
				if(results.value != parseFloat(curr_values["value"])&&!(typeof row.cells[4].getElementsByTagName("p")[0].style === 'undefined')){
					row.cells[4].getElementsByTagName("p")[0].style.color = 'green';
					//The above changes the colour of the displayed value to green so the user nows it has been changed from the original
					units_and_value_changed++;
					//console.log("COLOR CHANGED!");
				}
			}

			if(curr_values["units"] != ""){
				row.cells[5].getElementsByTagName("p")[0].innerHTML = results.units;
				if(results.units != curr_values["units"] && !(typeof row.cells[5].getElementsByTagName("p")[0].style === 'undefined')){
					row.cells[5].getElementsByTagName("p")[0].style.color = 'green';
					units_and_value_changed++;
					//console.log("COLOR CHANGED!");
				}
				if(curr_values["sym_err_units"] != "" && curr_values["sym_err_units"] != results.units && !(typeof row.cells[8].getElementsByTagName("p")[0].style === 'undefined')){
					row.cells[8].getElementsByTagName("p")[0].innerHTML = results.units;
					row.cells[8].getElementsByTagName("p")[0].style.color = 'green';
				}
			}
			if(units_and_value_changed == 2){//This would only occur if both the units and value on the display table were replaced by the converted versions
				var units_and_value = results.value.toString() + " " + results.units.toString();
				banner.getElementsByClassName("collapsiblebutton-vals")[0].getElementsByTagName("span")[j*2+1].innerHTML = units_and_value;
				banner.getElementsByClassName("collapsiblebutton-vals")[0].getElementsByTagName("span")[j*2+1].style.color = '#CBF1B2';//Slightly lighter green
			}
			
			var err_fields = ["symerr_conf", "asymerr"];
			for(var index = 0;index < err_fields.length; index++){
				if(curr_values[err_fields[index]] != ""){//This would mean there is no current value
					if(!(curr_values[err_fields[index]].includes('%'))){//A relative error isn't affected by the scalar multiplication that is unit conversion
						var rounded_new_value = round_values(curr_values[err_fields[index]], parseFloat(curr_values[err_fields[index]])*conversion_ratio);
						row.cells[fields[err_fields[index]]].getElementsByTagName("p")[0].innerHTML = rounded_new_value;

						if(rounded_new_value != curr_values[err_fields[index]] && !(typeof row.cells[fields[err_fields[index]]].getElementsByTagName("p")[0].style === 'undefined')){
							row.cells[fields[err_fields[index]]].getElementsByTagName("p")[0].style.color = 'green';
						}
					}
				}
			}
		}
	}
	console.log("Completed unit conversions");
	
}


function add_loading_icon(){
	loading_icon = document.getElementById("loading_icon");
	loading_icon.setAttribute("src", "./static/logos/loading_gif.jpg");
	console.log("Added the loading icon");
}

function remove_loading_icon(){
	loading_icon = document.getElementById("loading_icon");
	loading_icon.setAttribute("src", "");
	console.log("Removed the loading icon");
}

function round_values(orig_value, new_value){
	//This function is meant to round the converted value to the same number of significant figures as the original value.
	//It first counts the number of significant figures with var sig_figs, then returns the converted value to this precision
	
	var exponent = 0; //10^0 = 1 so the value will not be changed if no exponent is given
	if(orig_value.includes('e')){
		var i = orig_value.indexOf('e');
		exponent = parseInt(orig_value.substring(i+1, orig_value.length));//This would extract, for example 3 from +3 from e+3 or -3 from e-3
		orig_value = orig_value.substring(0, i);
	}
	
	var sides = orig_value.split(".");

	if(sides.length == 2){
		if(parseFloat(sides[0]) == 0.0){
			sig_figs = sides[1].length - leading_zeros(sides[1]);
			if(parseFloat(orig_value) == 0.0){sig_figs = orig_value.length -1;}
		}
		else{
			sig_figs = orig_value.length - leading_zeros(sides[0]) - 1; // -1 is for the decimal point
		}
	}
	else{
		var tailing_zeros = 0;
		for(var i = orig_value.length -1;orig_value[i] == '0' && i >= 0;i--){
			tailing_zeros++;
		}
		sig_figs = orig_value.length - leading_zeros(orig_value) - tailing_zeros;
		if(parseFloat(orig_value) == 0.0){sig_figs = 1;}
	}
	new_value = new_value.toPrecision(sig_figs).toString();
	if(new_value == parseFloat(orig_value)){
		return orig_value;
	}
	return new_value;
}

function leading_zeros(s){
	//This counts the number of 0s at the start of a string. It is used to count the number of signigifacnt figures of a value in round_values()
	var zs_count = 0;
	for(var i = 0;s[i] == '0' && i < s.length;i++){
		zs_count++;
	}
	return zs_count;
}

function empty_element_check(obj){
	//This is used to check if the current values in the measurement display table are present or not, as trying to extract the undefined values causes errors
	return !((typeof obj) === 'undefined' || (typeof obj.getElementsByTagName("p")[0]) === 'undefined');
}


//This object is used as the powers of 10 that each prefix corresponds to
var prefixes = {'k': 10.**3, 'c': 10.**(-2), 'm': 10.**(-3), 'u': 10.**(-6), 'n': 10.**(-9), 'p': 10.**(-12)};

var parts_per_prefixes = {'m': 10.**(-6), 'b': 10.**(-9), 't': 10.**(-12), 'q': 10.**(-15)};//The same as above, but for ppm, ppb, etc.

var Bq_to_g = {"U-238": 81.*10.**(-6), "Th-232": 246.*10.**(-6), "K-40": 32.3*10.**(-3), "U-235": 1.76*10.**(-3)};

var decay_chain_groups = {"U-238": ["Ra-226", "Pb-214", "Bi-214"], "Th-232": ["Pb-212", "Tl-208", "Ac-228"],
											"K-40": [], "U-235": []};


function standard_unit_factor(given_unit){
	//This function is based on converting all prefixed units to their base unit via a multiplication by some factor of 10
	//e.g 3.4 mBq/kg = 3.4x10^-6 Bq/g
		var units = given_unit.split("/");
		var factor = 1.0;//Factor represents this final factor of 10^n
		for(var index = 0;index < units.length;index++){
			var unit = units[index];
			var unit_factor = 1.0;
			if(unit[0] == 'm'){//Could be m as in metre or milli-
					if(unit.length==1||(unit.length==2 && is_numeric(unit[1]))){//the is_numeric would mean m2 or m3
							unit_factor = 1.0;
					}
					else{
							unit_factor = prefixes['m'];
					}
			}
			else if(unit[0] == 'p'){//Could be p as in ppm, ppb, etc., or pct, or pico-
					if(unit[1] == 'p'){
							unit_factor = parts_per_prefixes[unit[2]];
					}
					else if(unit == "pct"){
							unit_factor = 0.01;// corresponds to 10^-2
					}
					else{
							unit_factor = prefixes['p'];
					}
			}
			else{
				if(unit[0] in prefixes){
					unit_factor = prefixes[unit[0]];
				}
			}
			if(is_numeric(unit[unit.length - 1])){//For example m2 or m3
					unit_factor **= parseInt(unit[unit.length - 1]);
			}
			if(index == 0){
					factor *= unit_factor;
			}
			else{
					factor /= unit_factor;
			}
		}
		return factor;
}


function unit_type_factor(units, isotope){
	//This function is meant to find the Bq to g conversion specific to the isotope of the given measurement result
	var grouphead_isotope = "";
	if(Object.keys(Bq_to_g).includes(isotope)){
			grouphead_isotope = isotope;
	}
	else{
			for(var grouphead in Bq_to_g){
					if(decay_chain_groups[grouphead].includes(isotope)){
							grouphead_isotope = grouphead;
					}
			}
	}
	if(grouphead_isotope == ""){
			//console.log("Invalid isotope");
			return null;
			//This theoretically should never happen, as it would have been checked in isotope_convertable() in unit_conversion_main()
	}
	if(units.indexOf("Bq") !== -1){
			return Bq_to_g[grouphead_isotope];
	}
	return 1.0
}


function dimensionality_grouping(unit, error_check){
	//This is based on a grouping of units into one of 5 groups, in which only members within a group are dimensionally equal and can be converted to one another
	//The base units are 1: g, 2: g/g, 3: g/m, 4:g/m2, 5: g/m3. It is also assumed that Bq and g can be converted between one another
		var units = unit.split("/");
		if(units.length == 1){
				if(unit.includes("pp")||unit.includes("pct")){
						return 2;
				}
				return 1;
		}
		var last_char = unit.charAt(unit.length - 1)
		if(last_char == 'g'){return 2;}
		else if(last_char == 'm'){return 3;}
		else if(last_char == '2'){return 4;}
		else if(last_char == '3'){return 5;}
		return "Error" + error_check;
}

function is_numeric(character){
		return character <= '9' && character >= '0';
}

function type_units(current_units, final_units){
	//This is used to see if conversions that are simply a multiplication by some power of 10(e.g ppb to ppm) can still be done even if the Bq to g/g
	//conversion is not known for the given isotope
	if(current_units.includes("Bq") && final_units.includes("Bq"))
		return true;
	return (current_units.includes("pp") || current_units.includes("pct")) && (final_units.includes("pp") || final_units.includes("pct"));
}

function isotope_convertable(isotope){
	//This is checking if the Bq to g conversion is known for the given isotope
	if(Object.keys(Bq_to_g).includes(isotope)) return true;
	for(var chain_head in Bq_to_g){
		if(decay_chain_groups[chain_head].includes(isotope))
			return true;
	}
	return false;
}

function units_are_compatible(current_unit, final_unit){
	//This checks if the units are dimensionally compatible, as one cannot reasonably convert from Bq to Bq/m3 without more information
	//console.log(dimensionality_grouping(current_unit, "TI"), dimensionality_grouping(final_unit, "TO"));		
	return dimensionality_grouping(current_unit, "I") == dimensionality_grouping(final_unit, "O");
}

function unit_conversion_main(current_unit, final_unit, meas_value, isotope){
	//This is the main function from which all other functions directly involved in the unit conversions are called
	var returned_unit = current_unit;
	if(units_are_compatible(current_unit, final_unit)){
		var units_similarity = type_units(current_unit, final_unit);
		var conversion_factor = standard_unit_factor(current_unit);
		if(!units_similarity){//This means it is some form of a Bq to g conversion, which would require that isotope's conversion factor
			if(isotope_convertable(isotope)){
				conversion_factor *= unit_type_factor(current_unit, isotope);
				conversion_factor /= unit_type_factor(final_unit, isotope);
			}
			else{//If the isotope's conversion factor is not known, the original value and units are returned
				return {
					"value": meas_value,
					"units": current_unit
				}
			}
		}
		conversion_factor /= standard_unit_factor(final_unit);
		meas_value *= conversion_factor;
		returned_unit = final_unit;
	}
	return {
			"value": meas_value,
			"units": returned_unit
	};
}

console.log("Ready for unit conversion...");
//var results = unit_conversion_main("g/g", "pct", 1.0, "U-235")
//console.log(results)
