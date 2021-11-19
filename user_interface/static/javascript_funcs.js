function tryEnableSubmit() {
    if (validateDate() && validateIsotope()) {
        document.getElementById('submit-record-button').disabled = false;
    }
}

function validateDate() {
    var date_ele = document.querySelector('[name^="measurement.date"]');
    var date_val = date_ele.value

    // valid date formats: "%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y", "%Y-%d-%m", "%Y/%d/%m", "%d-%m-%Y", "%d/%m/%Y"
    var day_pattern = "(?:0[1-9]|1\\d|2\\d|3[0|1])";
    var month_pattern = "(?:0[1-9]|1[0|1|2])";
    var year_pattern = "(?:19|20)\\d{2}";

    var pos_a = date_val.search(year_pattern+"\\-"+month_pattern+"\\-"+day_pattern);
    var pos_b = date_val.search(year_pattern+"\\/"+month_pattern+"\\/"+day_pattern);
    var pos_c = date_val.search(month_pattern+"\\-"+day_pattern+"\\-"+year_pattern);
    var pos_d = date_val.search(month_pattern+"\\/"+day_pattern+"\\/"+year_pattern);
    var pos_e = date_val.search(year_pattern+"\\-"+day_pattern+"\\-"+month_pattern);
    var pos_f = date_val.search(year_pattern+"\\/"+day_pattern+"\\/"+month_pattern);
    var pos_g = date_val.search(day_pattern+"\\-"+month_pattern+"\\-"+year_pattern);
    var pos_h = date_val.search(day_pattern+"\\/"+month_pattern+"\\/"+year_pattern);
    var pos_i = date_val.search("^$");

    var date_invalid_tooltip = document.getElementById("invalid-meas-date-tooltip");
    var date_invalid_tooltip_text = document.getElementById("invalid-meas-date-tooltip-text");
    if (pos_a<0 && pos_b<0 && pos_c<0 && pos_d<0 && pos_e<0 && pos_f<0 && pos_g<0 && pos_h<0 && pos_i<0) {
        // invalid date format
        document.getElementById('submit-record-button').disabled = true;
        date_invalid_tooltip_text.style.visibility = "visible";
        return false;
    } else {
        date_invalid_tooltip_text.style.visibility = "hidden";
        return true;
    }
}

function validateIsotopes() {
    var isotopes = ["H-1","H-2","H-3","H-4","H-5","H-6","H-7","He-2","He-3","He-4","He-5","He-6","He-7","He-8","He-9","He-10","Li-3","Li-4","Li-5","Li-6","Li-7","Li-8","Li-9","Li-10","Li-11","Li-12","Be-5","Be-6","Be-7","Be-8","Be-9","Be-10","Be-11","Be-12","Be-13","Be-14","Be-15","Be-16","B-6","B-7","B-8","B-9","B-10","B-11","B-12","B-13","B-14","B-15","B-16","B-17","B-18","B-19","C-8","C-9","C-10","C-11","C-12","C-13","C-14","C-15","C-16","C-17","C-18","C-19","C-20","C-21","C-22","N-10","N-11","N-12","N-13","N-14","N-15","N-16","N-17","N-18","N-19","N-20","N-21","N-22","N-23","N-24","N-25","O-12","O-13","O-14","O-15","O-16","O-17","O-18","O-19","O-20","O-21","O-22","O-23","O-24","O-25","O-26","O-27","O-28","F-14","F-15","F-16","F-17","F-18","F-19","F-20","F-21","F-22","F-23","F-24","F-25","F-26","F-27","F-28","F-29","F-30","F-31","Ne-16","Ne-17","Ne-18","Ne-19","Ne-20","Ne-21","Ne-22","Ne-23","Ne-24","Ne-25","Ne-26","Ne-27","Ne-28","Ne-29","Ne-30","Ne-31","Ne-32","Ne-33","Ne-34","Na-18","Na-19","Na-20","Na-21","Na-22","Na-23","Na-24","Na-25","Na-26","Na-27","Na-28","Na-29","Na-30","Na-31","Na-32","Na-33","Na-34","Na-35","Na-36","Na-37","Mg-19","Mg-20","Mg-21","Mg-22","Mg-23","Mg-24","Mg-25","Mg-26","Mg-27","Mg-28","Mg-29","Mg-30","Mg-31","Mg-32","Mg-33","Mg-34","Mg-35","Mg-36","Mg-37","Mg-38","Mg-39","Mg-40","Al-21","Al-22","Al-23","Al-24","Al-25","Al-26","Al-27","Al-28","Al-29","Al-30","Al-31","Al-32","Al-33","Al-34","Al-35","Al-36","Al-37","Al-38","Al-39","Al-40","Al-41","Al-42","Si-22","Si-23","Si-24","Si-25","Si-26","Si-27","Si-28","Si-29","Si-30","Si-31","Si-32","Si-33","Si-34","Si-35","Si-36","Si-37","Si-38","Si-39","Si-40","Si-41","Si-42","Si-43","Si-44","P-24","P-25","P-26","P-27","P-28","P-29","P-30","P-31","P-32","P-33","P-34","P-35","P-36","P-37","P-38","P-39","P-40","P-41","P-42","P-43","P-44","P-45","P-46","S-26","S-27","S-28","S-29","S-30","S-31","S-32","S-33","S-34","S-35","S-36","S-37","S-38","S-39","S-40","S-41","S-42","S-43","S-44","S-45","S-46","S-47","S-48","S-49","Cl-28","Cl-29","Cl-30","Cl-31","Cl-32","Cl-33","Cl-34","Cl-35","Cl-36","Cl-37","Cl-38","Cl-39","Cl-40","Cl-41","Cl-42","Cl-43","Cl-44","Cl-45","Cl-46","Cl-47","Cl-48","Cl-49","Cl-50","Cl-51","Ar-30","Ar-31","Ar-32","Ar-33","Ar-34","Ar-35","Ar-36","Ar-37","Ar-38","Ar-39","Ar-40","Ar-41","Ar-42","Ar-43","Ar-44","Ar-45","Ar-46","Ar-47","Ar-48","Ar-49","Ar-50","Ar-51","Ar-52","Ar-53","K-32","K-33","K-34","K-35","K-36","K-37","K-38","K-39","K-40","K-41","K-42","K-43","K-44","K-45","K-46","K-47","K-48","K-49","K-50","K-51","K-52","K-53","K-54","K-55","Ca-34","Ca-35","Ca-36","Ca-37","Ca-38","Ca-39","Ca-40","Ca-41","Ca-42","Ca-43","Ca-44","Ca-45","Ca-46","Ca-47","Ca-48","Ca-49","Ca-50","Ca-51","Ca-52","Ca-53","Ca-54","Ca-55","Ca-56","Ca-57","Sc-36","Sc-37","Sc-38","Sc-39","Sc-40","Sc-41","Sc-42","Sc-43","Sc-44","Sc-45","Sc-46","Sc-47","Sc-48","Sc-49","Sc-50","Sc-51","Sc-52","Sc-53","Sc-54","Sc-55","Sc-56","Sc-57","Sc-58","Sc-59","Sc-60","Ti-38","Ti-39","Ti-40","Ti-41","Ti-42","Ti-43","Ti-44","Ti-45","Ti-46","Ti-47","Ti-48","Ti-49","Ti-50","Ti-51","Ti-52","Ti-53","Ti-54","Ti-55","Ti-56","Ti-57","Ti-58","Ti-59","Ti-60","Ti-61","Ti-62","Ti-63","V-40","V-41","V-42","V-43","V-44","V-45","V-46","V-47","V-48","V-49","V-50","V-51","V-52","V-53","V-54","V-55","V-56","V-57","V-58","V-59","V-60","V-61","V-62","V-63","V-64","V-65","Cr-42","Cr-43","Cr-44","Cr-45","Cr-46","Cr-47","Cr-48","Cr-49","Cr-50","Cr-51","Cr-52","Cr-53","Cr-54","Cr-55","Cr-56","Cr-57","Cr-58","Cr-59","Cr-60","Cr-61","Cr-62","Cr-63","Cr-64","Cr-65","Cr-66","Cr-67","Mn-44","Mn-45","Mn-46","Mn-47","Mn-48","Mn-49","Mn-50","Mn-51","Mn-52","Mn-53","Mn-54","Mn-55","Mn-56","Mn-57","Mn-58","Mn-59","Mn-60","Mn-61","Mn-62","Mn-63","Mn-64","Mn-65","Mn-66","Mn-67","Mn-68","Mn-69","Fe-45","Fe-46","Fe-47","Fe-48","Fe-49","Fe-50","Fe-51","Fe-52","Fe-53","Fe-54","Fe-55","Fe-56","Fe-57","Fe-58","Fe-59","Fe-60","Fe-61","Fe-62","Fe-63","Fe-64","Fe-65","Fe-66","Fe-67","Fe-68","Fe-69","Fe-70","Fe-71","Fe-72","Co-47","Co-48","Co-49","Co-50","Co-51","Co-52","Co-53","Co-54","Co-55","Co-56","Co-57","Co-58","Co-59","Co-60","Co-61","Co-62","Co-63","Co-64","Co-65","Co-66","Co-67","Co-68","Co-69","Co-70","Co-71","Co-72","Co-73","Co-74","Co-75","Ni-48","Ni-49","Ni-50","Ni-51","Ni-52","Ni-53","Ni-54","Ni-55","Ni-56","Ni-57","Ni-58","Ni-59","Ni-60","Ni-61","Ni-62","Ni-63","Ni-64","Ni-65","Ni-66","Ni-67","Ni-68","Ni-69","Ni-70","Ni-71","Ni-72","Ni-73","Ni-74","Ni-75","Ni-76","Ni-77","Ni-78","Cu-52","Cu-53","Cu-54","Cu-55","Cu-56","Cu-57","Cu-58","Cu-59","Cu-60","Cu-61","Cu-62","Cu-63","Cu-64","Cu-65","Cu-66","Cu-67","Cu-68","Cu-69","Cu-70","Cu-71","Cu-72","Cu-73","Cu-74","Cu-75","Cu-76","Cu-77","Cu-78","Cu-79","Cu-80","Zn-54","Zn-55","Zn-56","Zn-57","Zn-58","Zn-59","Zn-60","Zn-61","Zn-62","Zn-63","Zn-64","Zn-65","Zn-66","Zn-67","Zn-68","Zn-69","Zn-70","Zn-71","Zn-72","Zn-73","Zn-74","Zn-75","Zn-76","Zn-77","Zn-78","Zn-79","Zn-80","Zn-81","Zn-82","Zn-83","Ga-56","Ga-57","Ga-58","Ga-59","Ga-60","Ga-61","Ga-62","Ga-63","Ga-64","Ga-65","Ga-66","Ga-67","Ga-68","Ga-69","Ga-70","Ga-71","Ga-72","Ga-73","Ga-74","Ga-75","Ga-76","Ga-77","Ga-78","Ga-79","Ga-80","Ga-81","Ga-82","Ga-83","Ga-84","Ga-85","Ga-86","Ge-58","Ge-59","Ge-60","Ge-61","Ge-62","Ge-63","Ge-64","Ge-65","Ge-66","Ge-67","Ge-68","Ge-69","Ge-70","Ge-71","Ge-72","Ge-73","Ge-74","Ge-75","Ge-76","Ge-77","Ge-78","Ge-79","Ge-80","Ge-81","Ge-82","Ge-83","Ge-84","Ge-85","Ge-86","Ge-87","Ge-88","Ge-89","As-60","As-61","As-62","As-63","As-64","As-65","As-66","As-67","As-68","As-69","As-70","As-71","As-72","As-73","As-74","As-75","As-76","As-77","As-78","As-79","As-80","As-81","As-82","As-83","As-84","As-85","As-86","As-87","As-88","As-89","As-90","As-91","As-92","Se-65","Se-66","Se-67","Se-68","Se-69","Se-70","Se-71","Se-72","Se-73","Se-74","Se-75","Se-76","Se-77","Se-78","Se-79","Se-80","Se-81","Se-82","Se-83","Se-84","Se-85","Se-86","Se-87","Se-88","Se-89","Se-90","Se-91","Se-92","Se-93","Se-94","Br-67","Br-68","Br-69","Br-70","Br-71","Br-72","Br-73","Br-74","Br-75","Br-76","Br-77","Br-78","Br-79","Br-80","Br-81","Br-82","Br-83","Br-84","Br-85","Br-86","Br-87","Br-88","Br-89","Br-90","Br-91","Br-92","Br-93","Br-94","Br-95","Br-96","Br-97","Kr-69","Kr-70","Kr-71","Kr-72","Kr-73","Kr-74","Kr-75","Kr-76","Kr-77","Kr-78","Kr-79","Kr-80","Kr-81","Kr-82","Kr-83","Kr-84","Kr-85","Kr-86","Kr-87","Kr-88","Kr-89","Kr-90","Kr-91","Kr-92","Kr-93","Kr-94","Kr-95","Kr-96","Kr-97","Kr-98","Kr-99","Kr-100","Rb-71","Rb-72","Rb-73","Rb-74","Rb-75","Rb-76","Rb-77","Rb-78","Rb-79","Rb-80","Rb-81","Rb-82","Rb-83","Rb-84","Rb-85","Rb-86","Rb-87","Rb-88","Rb-89","Rb-90","Rb-91","Rb-92","Rb-93","Rb-94","Rb-95","Rb-96","Rb-97","Rb-98","Rb-99","Rb-100","Rb-101","Rb-102","Sr-73","Sr-74","Sr-75","Sr-76","Sr-77","Sr-78","Sr-79","Sr-80","Sr-81","Sr-82","Sr-83","Sr-84","Sr-85","Sr-86","Sr-87","Sr-88","Sr-89","Sr-90","Sr-91","Sr-92","Sr-93","Sr-94","Sr-95","Sr-96","Sr-97","Sr-98","Sr-99","Sr-100","Sr-101","Sr-102","Sr-103","Sr-104","Sr-105","Y-76","Y-77","Y-78","Y-79","Y-80","Y-81","Y-82","Y-83","Y-84","Y-85","Y-86","Y-87","Y-88","Y-89","Y-90","Y-91","Y-92","Y-93","Y-94","Y-95","Y-96","Y-97","Y-98","Y-99","Y-100","Y-101","Y-102","Y-103","Y-104","Y-105","Y-106","Y-107","Y-108","Zr-78","Zr-79","Zr-80","Zr-81","Zr-82","Zr-83","Zr-84","Zr-85","Zr-86","Zr-87","Zr-88","Zr-89","Zr-90","Zr-91","Zr-92","Zr-93","Zr-94","Zr-95","Zr-96","Zr-97","Zr-98","Zr-99","Zr-100","Zr-101","Zr-102","Zr-103","Zr-104","Zr-105","Zr-106","Zr-107","Zr-108","Zr-109","Zr-110","Nb-81","Nb-82","Nb-83","Nb-84","Nb-85","Nb-86","Nb-87","Nb-88","Nb-89","Nb-90","Nb-91","Nb-92","Nb-93","Nb-94","Nb-95","Nb-96","Nb-97","Nb-98","Nb-99","Nb-100","Nb-101","Nb-102","Nb-103","Nb-104","Nb-105","Nb-106","Nb-107","Nb-108","Nb-109","Nb-110","Nb-111","Nb-112","Nb-113","Mo-83","Mo-84","Mo-85","Mo-86","Mo-87","Mo-88","Mo-89","Mo-90","Mo-91","Mo-92","Mo-93","Mo-94","Mo-95","Mo-96","Mo-97","Mo-98","Mo-99","Mo-100","Mo-101","Mo-102","Mo-103","Mo-104","Mo-105","Mo-106","Mo-107","Mo-108","Mo-109","Mo-110","Mo-111","Mo-112","Mo-113","Mo-114","Mo-115","Tc-85","Tc-86","Tc-87","Tc-88","Tc-89","Tc-90","Tc-91","Tc-92","Tc-93","Tc-94","Tc-95","Tc-96","Tc-97","Tc-98","Tc-99","Tc-100","Tc-101","Tc-102","Tc-103","Tc-104","Tc-105","Tc-106","Tc-107","Tc-108","Tc-109","Tc-110","Tc-111","Tc-112","Tc-113","Tc-114","Tc-115","Tc-116","Tc-117","Tc-118","Ru-87","Ru-88","Ru-89","Ru-90","Ru-91","Ru-92","Ru-93","Ru-94","Ru-95","Ru-96","Ru-97","Ru-98","Ru-99","Ru-100","Ru-101","Ru-102","Ru-103","Ru-104","Ru-105","Ru-106","Ru-107","Ru-108","Ru-109","Ru-110","Ru-111","Ru-112","Ru-113","Ru-114","Ru-115","Ru-116","Ru-117","Ru-118","Ru-119","Ru-120","Rh-89","Rh-90","Rh-91","Rh-92","Rh-93","Rh-94","Rh-95","Rh-96","Rh-97","Rh-98","Rh-99","Rh-100","Rh-101","Rh-102","Rh-103","Rh-104","Rh-105","Rh-106","Rh-107","Rh-108","Rh-109","Rh-110","Rh-111","Rh-112","Rh-113","Rh-114","Rh-115","Rh-116","Rh-117","Rh-118","Rh-119","Rh-120","Rh-121","Rh-122","Pd-91","Pd-92","Pd-93","Pd-94","Pd-95","Pd-96","Pd-97","Pd-98","Pd-99","Pd-100","Pd-101","Pd-102","Pd-103","Pd-104","Pd-105","Pd-106","Pd-107","Pd-108","Pd-109","Pd-110","Pd-111","Pd-112","Pd-113","Pd-114","Pd-115","Pd-116","Pd-117","Pd-118","Pd-119","Pd-120","Pd-121","Pd-122","Pd-123","Pd-124","Ag-93","Ag-94","Ag-95","Ag-96","Ag-97","Ag-98","Ag-99","Ag-100","Ag-101","Ag-102","Ag-103","Ag-104","Ag-105","Ag-106","Ag-107","Ag-108","Ag-109","Ag-110","Ag-111","Ag-112","Ag-113","Ag-114","Ag-115","Ag-116","Ag-117","Ag-118","Ag-119","Ag-120","Ag-121","Ag-122","Ag-123","Ag-124","Ag-125","Ag-126","Ag-127","Ag-128","Ag-129","Ag-130","Cd-95","Cd-96","Cd-97","Cd-98","Cd-99","Cd-100","Cd-101","Cd-102","Cd-103","Cd-104","Cd-105","Cd-106","Cd-107","Cd-108","Cd-109","Cd-110","Cd-111","Cd-112","Cd-113","Cd-114","Cd-115","Cd-116","Cd-117","Cd-118","Cd-119","Cd-120","Cd-121","Cd-122","Cd-123","Cd-124","Cd-125","Cd-126","Cd-127","Cd-128","Cd-129","Cd-130","Cd-131","Cd-132","In-97","In-98","In-99","In-100","In-101","In-102","In-103","In-104","In-105","In-106","In-107","In-108","In-109","In-110","In-111","In-112","In-113","In-114","In-115","In-116","In-117","In-118","In-119","In-120","In-121","In-122","In-123","In-124","In-125","In-126","In-127","In-128","In-129","In-130","In-131","In-132","In-133","In-134","In-135","Sn-99","Sn-100","Sn-101","Sn-102","Sn-103","Sn-104","Sn-105","Sn-106","Sn-107","Sn-108","Sn-109","Sn-110","Sn-111","Sn-112","Sn-113","Sn-114","Sn-115","Sn-116","Sn-117","Sn-118","Sn-119","Sn-120","Sn-121","Sn-122","Sn-123","Sn-124","Sn-125","Sn-126","Sn-127","Sn-128","Sn-129","Sn-130","Sn-131","Sn-132","Sn-133","Sn-134","Sn-135","Sn-136","Sn-137","Sb-103","Sb-104","Sb-105","Sb-106","Sb-107","Sb-108","Sb-109","Sb-110","Sb-111","Sb-112","Sb-113","Sb-114","Sb-115","Sb-116","Sb-117","Sb-118","Sb-119","Sb-120","Sb-121","Sb-122","Sb-123","Sb-124","Sb-125","Sb-126","Sb-127","Sb-128","Sb-129","Sb-130","Sb-131","Sb-132","Sb-133","Sb-134","Sb-135","Sb-136","Sb-137","Sb-138","Sb-139","Te-105","Te-106","Te-107","Te-108","Te-109","Te-110","Te-111","Te-112","Te-113","Te-114","Te-115","Te-116","Te-117","Te-118","Te-119","Te-120","Te-121","Te-122","Te-123","Te-124","Te-125","Te-126","Te-127","Te-128","Te-129","Te-130","Te-131","Te-132","Te-133","Te-134","Te-135","Te-136","Te-137","Te-138","Te-139","Te-140","Te-141","Te-142","I-108","I-109","I-110","I-111","I-112","I-113","I-114","I-115","I-116","I-117","I-118","I-119","I-120","I-121","I-122","I-123","I-124","I-125","I-126","I-127","I-128","I-129","I-130","I-131","I-132","I-133","I-134","I-135","I-136","I-137","I-138","I-139","I-140","I-141","I-142","I-143","I-144","Xe-110","Xe-111","Xe-112","Xe-113","Xe-114","Xe-115","Xe-116","Xe-117","Xe-118","Xe-119","Xe-120","Xe-121","Xe-122","Xe-123","Xe-124","Xe-125","Xe-126","Xe-127","Xe-128","Xe-129","Xe-130","Xe-131","Xe-132","Xe-133","Xe-134","Xe-135","Xe-136","Xe-137","Xe-138","Xe-139","Xe-140","Xe-141","Xe-142","Xe-143","Xe-144","Xe-145","Xe-146","Xe-147","Cs-112","Cs-113","Cs-114","Cs-115","Cs-116","Cs-117","Cs-118","Cs-119","Cs-120","Cs-121","Cs-122","Cs-123","Cs-124","Cs-125","Cs-126","Cs-127","Cs-128","Cs-129","Cs-130","Cs-131","Cs-132","Cs-133","Cs-134","Cs-135","Cs-136","Cs-137","Cs-138","Cs-139","Cs-140","Cs-141","Cs-142","Cs-143","Cs-144","Cs-145","Cs-146","Cs-147","Cs-148","Cs-149","Cs-150","Cs-151","Ba-114","Ba-115","Ba-116","Ba-117","Ba-118","Ba-119","Ba-120","Ba-121","Ba-122","Ba-123","Ba-124","Ba-125","Ba-126","Ba-127","Ba-128","Ba-129","Ba-130","Ba-131","Ba-132","Ba-133","Ba-134","Ba-135","Ba-136","Ba-137","Ba-138","Ba-139","Ba-140","Ba-141","Ba-142","Ba-143","Ba-144","Ba-145","Ba-146","Ba-147","Ba-148","Ba-149","Ba-150","Ba-151","Ba-152","Ba-153","La-117","La-118","La-119","La-120","La-121","La-122","La-123","La-124","La-125","La-126","La-127","La-128","La-129","La-130","La-131","La-132","La-133","La-134","La-135","La-136","La-137","La-138","La-139","La-140","La-141","La-142","La-143","La-144","La-145","La-146","La-147","La-148","La-149","La-150","La-151","La-152","La-153","La-154","La-155","Ce-119","Ce-120","Ce-121","Ce-122","Ce-123","Ce-124","Ce-125","Ce-126","Ce-127","Ce-128","Ce-129","Ce-130","Ce-131","Ce-132","Ce-133","Ce-134","Ce-135","Ce-136","Ce-137","Ce-138","Ce-139","Ce-140","Ce-141","Ce-142","Ce-143","Ce-144","Ce-145","Ce-146","Ce-147","Ce-148","Ce-149","Ce-150","Ce-151","Ce-152","Ce-153","Ce-154","Ce-155","Ce-156","Ce-157","Pr-121","Pr-122","Pr-123","Pr-124","Pr-125","Pr-126","Pr-127","Pr-128","Pr-129","Pr-130","Pr-131","Pr-132","Pr-133","Pr-134","Pr-135","Pr-136","Pr-137","Pr-138","Pr-139","Pr-140","Pr-141","Pr-142","Pr-143","Pr-144","Pr-145","Pr-146","Pr-147","Pr-148","Pr-149","Pr-150","Pr-151","Pr-152","Pr-153","Pr-154","Pr-155","Pr-156","Pr-157","Pr-158","Pr-159","Nd-124","Nd-125","Nd-126","Nd-127","Nd-128","Nd-129","Nd-130","Nd-131","Nd-132","Nd-133","Nd-134","Nd-135","Nd-136","Nd-137","Nd-138","Nd-139","Nd-140","Nd-141","Nd-142","Nd-143","Nd-144","Nd-145","Nd-146","Nd-147","Nd-148","Nd-149","Nd-150","Nd-151","Nd-152","Nd-153","Nd-154","Nd-155","Nd-156","Nd-157","Nd-158","Nd-159","Nd-160","Nd-161","Pm-126","Pm-127","Pm-128","Pm-129","Pm-130","Pm-131","Pm-132","Pm-133","Pm-134","Pm-135","Pm-136","Pm-137","Pm-138","Pm-139","Pm-140","Pm-141","Pm-142","Pm-143","Pm-144","Pm-145","Pm-146","Pm-147","Pm-148","Pm-149","Pm-150","Pm-151","Pm-152","Pm-153","Pm-154","Pm-155","Pm-156","Pm-157","Pm-158","Pm-159","Pm-160","Pm-161","Pm-162","Pm-163","Sm-128","Sm-129","Sm-130","Sm-131","Sm-132","Sm-133","Sm-134","Sm-135","Sm-136","Sm-137","Sm-138","Sm-139","Sm-140","Sm-141","Sm-142","Sm-143","Sm-144","Sm-145","Sm-146","Sm-147","Sm-148","Sm-149","Sm-150","Sm-151","Sm-152","Sm-153","Sm-154","Sm-155","Sm-156","Sm-157","Sm-158","Sm-159","Sm-160","Sm-161","Sm-162","Sm-163","Sm-164","Sm-165","Eu-130","Eu-131","Eu-132","Eu-133","Eu-134","Eu-135","Eu-136","Eu-137","Eu-138","Eu-139","Eu-140","Eu-141","Eu-142","Eu-143","Eu-144","Eu-145","Eu-146","Eu-147","Eu-148","Eu-149","Eu-150","Eu-151","Eu-152","Eu-153","Eu-154","Eu-155","Eu-156","Eu-157","Eu-158","Eu-159","Eu-160","Eu-161","Eu-162","Eu-163","Eu-164","Eu-165","Eu-166","Eu-167","Gd-134","Gd-135","Gd-136","Gd-137","Gd-138","Gd-139","Gd-140","Gd-141","Gd-142","Gd-143","Gd-144","Gd-145","Gd-146","Gd-147","Gd-148","Gd-149","Gd-150","Gd-151","Gd-152","Gd-153","Gd-154","Gd-155","Gd-156","Gd-157","Gd-158","Gd-159","Gd-160","Gd-161","Gd-162","Gd-163","Gd-164","Gd-165","Gd-166","Gd-167","Gd-168","Gd-169","Tb-136","Tb-137","Tb-138","Tb-139","Tb-140","Tb-141","Tb-142","Tb-143","Tb-144","Tb-145","Tb-146","Tb-147","Tb-148","Tb-149","Tb-150","Tb-151","Tb-152","Tb-153","Tb-154","Tb-155","Tb-156","Tb-157","Tb-158","Tb-159","Tb-160","Tb-161","Tb-162","Tb-163","Tb-164","Tb-165","Tb-166","Tb-167","Tb-168","Tb-169","Tb-170","Tb-171","Dy-138","Dy-139","Dy-140","Dy-141","Dy-142","Dy-143","Dy-144","Dy-145","Dy-146","Dy-147","Dy-148","Dy-149","Dy-150","Dy-151","Dy-152","Dy-153","Dy-154","Dy-155","Dy-156","Dy-157","Dy-158","Dy-159","Dy-160","Dy-161","Dy-162","Dy-163","Dy-164","Dy-165","Dy-166","Dy-167","Dy-168","Dy-169","Dy-170","Dy-171","Dy-172","Dy-173","Ho-140","Ho-141","Ho-142","Ho-143","Ho-144","Ho-145","Ho-146","Ho-147","Ho-148","Ho-149","Ho-150","Ho-151","Ho-152","Ho-153","Ho-154","Ho-155","Ho-156","Ho-157","Ho-158","Ho-159","Ho-160","Ho-161","Ho-162","Ho-163","Ho-164","Ho-165","Ho-166","Ho-167","Ho-168","Ho-169","Ho-170","Ho-171","Ho-172","Ho-173","Ho-174","Ho-175","Er-143","Er-144","Er-145","Er-146","Er-147","Er-148","Er-149","Er-150","Er-151","Er-152","Er-153","Er-154","Er-155","Er-156","Er-157","Er-158","Er-159","Er-160","Er-161","Er-162","Er-163","Er-164","Er-165","Er-166","Er-167","Er-168","Er-169","Er-170","Er-171","Er-172","Er-173","Er-174","Er-175","Er-176","Er-177","Tm-145","Tm-146","Tm-147","Tm-148","Tm-149","Tm-150","Tm-151","Tm-152","Tm-153","Tm-154","Tm-155","Tm-156","Tm-157","Tm-158","Tm-159","Tm-160","Tm-161","Tm-162","Tm-163","Tm-164","Tm-165","Tm-166","Tm-167","Tm-168","Tm-169","Tm-170","Tm-171","Tm-172","Tm-173","Tm-174","Tm-175","Tm-176","Tm-177","Tm-178","Tm-179","Yb-148","Yb-149","Yb-150","Yb-151","Yb-152","Yb-153","Yb-154","Yb-155","Yb-156","Yb-157","Yb-158","Yb-159","Yb-160","Yb-161","Yb-162","Yb-163","Yb-164","Yb-165","Yb-166","Yb-167","Yb-168","Yb-169","Yb-170","Yb-171","Yb-172","Yb-173","Yb-174","Yb-175","Yb-176","Yb-177","Yb-178","Yb-179","Yb-180","Yb-181","Yb-182","Lu-150","Lu-151","Lu-152","Lu-153","Lu-154","Lu-155","Lu-156","Lu-157","Lu-158","Lu-159","Lu-160","Lu-161","Lu-162","Lu-163","Lu-164","Lu-165","Lu-166","Lu-167","Lu-168","Lu-169","Lu-170","Lu-171","Lu-172","Lu-173","Lu-174","Lu-175","Lu-176","Lu-177","Lu-178","Lu-179","Lu-180","Lu-181","Lu-182","Lu-183","Lu-184","Hf-153","Hf-154","Hf-155","Hf-156","Hf-157","Hf-158","Hf-159","Hf-160","Hf-161","Hf-162","Hf-163","Hf-164","Hf-165","Hf-166","Hf-167","Hf-168","Hf-169","Hf-170","Hf-171","Hf-172","Hf-173","Hf-174","Hf-175","Hf-176","Hf-177","Hf-178","Hf-179","Hf-180","Hf-181","Hf-182","Hf-183","Hf-184","Hf-185","Hf-186","Hf-187","Hf-188","Ta-155","Ta-156","Ta-157","Ta-158","Ta-159","Ta-160","Ta-161","Ta-162","Ta-163","Ta-164","Ta-165","Ta-166","Ta-167","Ta-168","Ta-169","Ta-170","Ta-171","Ta-172","Ta-173","Ta-174","Ta-175","Ta-176","Ta-177","Ta-178","Ta-179","Ta-180","Ta-181","Ta-182","Ta-183","Ta-184","Ta-185","Ta-186","Ta-187","Ta-188","Ta-189","Ta-190","W-158","W-159","W-160","W-161","W-162","W-163","W-164","W-165","W-166","W-167","W-168","W-169","W-170","W-171","W-172","W-173","W-174","W-175","W-176","W-177","W-178","W-179","W-180","W-181","W-182","W-183","W-184","W-185","W-186","W-187","W-188","W-189","W-190","W-191","W-192","Re-160","Re-161","Re-162","Re-163","Re-164","Re-165","Re-166","Re-167","Re-168","Re-169","Re-170","Re-171","Re-172","Re-173","Re-174","Re-175","Re-176","Re-177","Re-178","Re-179","Re-180","Re-181","Re-182","Re-183","Re-184","Re-185","Re-186","Re-187","Re-188","Re-189","Re-190","Re-191","Re-192","Re-193","Re-194","Os-162","Os-163","Os-164","Os-165","Os-166","Os-167","Os-168","Os-169","Os-170","Os-171","Os-172","Os-173","Os-174","Os-175","Os-176","Os-177","Os-178","Os-179","Os-180","Os-181","Os-182","Os-183","Os-184","Os-185","Os-186","Os-187","Os-188","Os-189","Os-190","Os-191","Os-192","Os-193","Os-194","Os-195","Os-196","Ir-164","Ir-165","Ir-166","Ir-167","Ir-168","Ir-169","Ir-170","Ir-171","Ir-172","Ir-173","Ir-174","Ir-175","Ir-176","Ir-177","Ir-178","Ir-179","Ir-180","Ir-181","Ir-182","Ir-183","Ir-184","Ir-185","Ir-186","Ir-187","Ir-188","Ir-189","Ir-190","Ir-191","Ir-192","Ir-193","Ir-194","Ir-195","Ir-196","Ir-197","Ir-198","Ir-199","Pt-166","Pt-167","Pt-168","Pt-169","Pt-170","Pt-171","Pt-172","Pt-173","Pt-174","Pt-175","Pt-176","Pt-177","Pt-178","Pt-179","Pt-180","Pt-181","Pt-182","Pt-183","Pt-184","Pt-185","Pt-186","Pt-187","Pt-188","Pt-189","Pt-190","Pt-191","Pt-192","Pt-193","Pt-194","Pt-195","Pt-196","Pt-197","Pt-198","Pt-199","Pt-200","Pt-201","Pt-202","Au-169","Au-170","Au-171","Au-172","Au-173","Au-174","Au-175","Au-176","Au-177","Au-178","Au-179","Au-180","Au-181","Au-182","Au-183","Au-184","Au-185","Au-186","Au-187","Au-188","Au-189","Au-190","Au-191","Au-192","Au-193","Au-194","Au-195","Au-196","Au-197","Au-198","Au-199","Au-200","Au-201","Au-202","Au-203","Au-204","Au-205","Hg-171","Hg-172","Hg-173","Hg-174","Hg-175","Hg-176","Hg-177","Hg-178","Hg-179","Hg-180","Hg-181","Hg-182","Hg-183","Hg-184","Hg-185","Hg-186","Hg-187","Hg-188","Hg-189","Hg-190","Hg-191","Hg-192","Hg-193","Hg-194","Hg-195","Hg-196","Hg-197","Hg-198","Hg-199","Hg-200","Hg-201","Hg-202","Hg-203","Hg-204","Hg-205","Hg-206","Hg-207","Hg-208","Hg-209","Hg-210","Tl-176","Tl-177","Tl-178","Tl-179","Tl-180","Tl-181","Tl-182","Tl-183","Tl-184","Tl-185","Tl-186","Tl-187","Tl-188","Tl-189","Tl-190","Tl-191","Tl-192","Tl-193","Tl-194","Tl-195","Tl-196","Tl-197","Tl-198","Tl-199","Tl-200","Tl-201","Tl-202","Tl-203","Tl-204","Tl-205","Tl-206","Tl-207","Tl-208","Tl-209","Tl-210","Tl-211","Tl-212","Pb-178","Pb-179","Pb-180","Pb-181","Pb-182","Pb-183","Pb-184","Pb-185","Pb-186","Pb-187","Pb-188","Pb-189","Pb-190","Pb-191","Pb-192","Pb-193","Pb-194","Pb-195","Pb-196","Pb-197","Pb-198","Pb-199","Pb-200","Pb-201","Pb-202","Pb-203","Pb-204","Pb-205","Pb-206","Pb-207","Pb-208","Pb-209","Pb-210","Pb-211","Pb-212","Pb-213","Pb-214","Pb-215","Bi-184","Bi-185","Bi-186","Bi-187","Bi-188","Bi-189","Bi-190","Bi-191","Bi-192","Bi-193","Bi-194","Bi-195","Bi-196","Bi-197","Bi-198","Bi-199","Bi-200","Bi-201","Bi-202","Bi-203","Bi-204","Bi-205","Bi-206","Bi-207","Bi-208","Bi-209","Bi-210","Bi-211","Bi-212","Bi-213","Bi-214","Bi-215","Bi-216","Bi-217","Bi-218","Bi-219","Po-188","Po-189","Po-190","Po-191","Po-192","Po-193","Po-194","Po-195","Po-196","Po-197","Po-198","Po-199","Po-200","Po-201","Po-202","Po-203","Po-204","Po-205","Po-206","Po-207","Po-208","Po-209","Po-210","Po-211","Po-212","Po-213","Po-214","Po-215","Po-216","Po-217","Po-218","Po-219","Po-220","At-193","At-194","At-195","At-196","At-197","At-198","At-199","At-200","At-201","At-202","At-203","At-204","At-205","At-206","At-207","At-208","At-209","At-210","At-211","At-212","At-213","At-214","At-215","At-216","At-217","At-218","At-219","At-220","At-221","At-222","At-223","Rn-195","Rn-196","Rn-197","Rn-198","Rn-199","Rn-200","Rn-201","Rn-202","Rn-203","Rn-204","Rn-205","Rn-206","Rn-207","Rn-208","Rn-209","Rn-210","Rn-211","Rn-212","Rn-213","Rn-214","Rn-215","Rn-216","Rn-217","Rn-218","Rn-219","Rn-220","Rn-221","Rn-222","Rn-223","Rn-224","Rn-225","Rn-226","Rn-227","Rn-228","Fr-199","Fr-200","Fr-201","Fr-202","Fr-203","Fr-204","Fr-205","Fr-206","Fr-207","Fr-208","Fr-209","Fr-210","Fr-211","Fr-212","Fr-213","Fr-214","Fr-215","Fr-216","Fr-217","Fr-218","Fr-219","Fr-220","Fr-221","Fr-222","Fr-223","Fr-224","Fr-225","Fr-226","Fr-227","Fr-228","Fr-229","Fr-230","Fr-231","Fr-232","Ra-202","Ra-203","Ra-204","Ra-205","Ra-206","Ra-207","Ra-208","Ra-209","Ra-210","Ra-211","Ra-212","Ra-213","Ra-214","Ra-215","Ra-216","Ra-217","Ra-218","Ra-219","Ra-220","Ra-221","Ra-222","Ra-223","Ra-224","Ra-225","Ra-226","Ra-227","Ra-228","Ra-229","Ra-230","Ra-231","Ra-232","Ra-233","Ra-234","Ac-206","Ac-207","Ac-208","Ac-209","Ac-210","Ac-211","Ac-212","Ac-213","Ac-214","Ac-215","Ac-216","Ac-217","Ac-218","Ac-219","Ac-220","Ac-221","Ac-222","Ac-223","Ac-224","Ac-225","Ac-226","Ac-227","Ac-228","Ac-229","Ac-230","Ac-231","Ac-232","Ac-233","Ac-234","Ac-235","Ac-236","Th-209","Th-210","Th-211","Th-212","Th-213","Th-214","Th-215","Th-216","Th-217","Th-218","Th-219","Th-220","Th-221","Th-222","Th-223","Th-224","Th-225","Th-226","Th-227","Th-228","Th-229","Th-230","Th-231","Th-232","Th-233","Th-234","Th-235","Th-236","Th-237","Th-238","Pa-212","Pa-213","Pa-214","Pa-215","Pa-216","Pa-217","Pa-218","Pa-219","Pa-220","Pa-221","Pa-222","Pa-223","Pa-224","Pa-225","Pa-226","Pa-227","Pa-228","Pa-229","Pa-230","Pa-231","Pa-232","Pa-233","Pa-234","Pa-235","Pa-236","Pa-237","Pa-238","Pa-239","Pa-240","U-217","U-218","U-219","U-220","U-221","U-222","U-223","U-224","U-225","U-226","U-227","U-228","U-229","U-230","U-231","U-232","U-233","U-234","U-235","U-236","U-237","U-238","U-239","U-240","U-241","U-242","Np-225","Np-226","Np-227","Np-228","Np-229","Np-230","Np-231","Np-232","Np-233","Np-234","Np-235","Np-236","Np-237","Np-238","Np-239","Np-240","Np-241","Np-242","Np-243","Np-244","Pu-228","Pu-229","Pu-230","Pu-231","Pu-232","Pu-233","Pu-234","Pu-235","Pu-236","Pu-237","Pu-238","Pu-239","Pu-240","Pu-241","Pu-242","Pu-243","Pu-244","Pu-245","Pu-246","Pu-247","Am-231","Am-232","Am-233","Am-234","Am-235","Am-236","Am-237","Am-238","Am-239","Am-240","Am-241","Am-242","Am-243","Am-244","Am-245","Am-246","Am-247","Am-248","Am-249","Cm-233","Cm-234","Cm-235","Cm-236","Cm-237","Cm-238","Cm-239","Cm-240","Cm-241","Cm-242","Cm-243","Cm-244","Cm-245","Cm-246","Cm-247","Cm-248","Cm-249","Cm-250","Cm-251","Cm-252","Bk-235","Bk-236","Bk-237","Bk-238","Bk-239","Bk-240","Bk-241","Bk-242","Bk-243","Bk-244","Bk-245","Bk-246","Bk-247","Bk-248","Bk-249","Bk-250","Bk-251","Bk-252","Bk-253","Bk-254","Cf-237","Cf-238","Cf-239","Cf-240","Cf-241","Cf-242","Cf-243","Cf-244","Cf-245","Cf-246","Cf-247","Cf-248","Cf-249","Cf-250","Cf-251","Cf-252","Cf-253","Cf-254","Cf-255","Cf-256","Es-240","Es-241","Es-242","Es-243","Es-244","Es-245","Es-246","Es-247","Es-248","Es-249","Es-250","Es-251","Es-252","Es-253","Es-254","Es-255","Es-256","Es-257","Es-258","Fm-242","Fm-243","Fm-244","Fm-245","Fm-246","Fm-247","Fm-248","Fm-249","Fm-250","Fm-251","Fm-252","Fm-253","Fm-254","Fm-255","Fm-256","Fm-257","Fm-258","Fm-259","Fm-260","Md-245","Md-246","Md-247","Md-248","Md-249","Md-250","Md-251","Md-252","Md-253","Md-254","Md-255","Md-256","Md-257","Md-258","Md-259","Md-260","Md-261","Md-262","No-248","No-249","No-250","No-251","No-252","No-253","No-254","No-255","No-256","No-257","No-258","No-259","No-260","No-261","No-262","No-263","No-264","Lr-251","Lr-252","Lr-253","Lr-254","Lr-255","Lr-256","Lr-257","Lr-258","Lr-259","Lr-260","Lr-261","Lr-262","Lr-263","Lr-264","Lr-265","Lr-266","Rf-253","Rf-254","Rf-255","Rf-256","Rf-257","Rf-258","Rf-259","Rf-260","Rf-261","Rf-262","Rf-263","Rf-264","Rf-265","Rf-266","Rf-267","Rf-268","Db-255","Db-256","Db-257","Db-258","Db-259","Db-260","Db-261","Db-262","Db-263","Db-264","Db-265","Db-266","Db-267","Db-268","Db-269","Db-270","Sg-258","Sg-259","Sg-260","Sg-261","Sg-262","Sg-263","Sg-264","Sg-265","Sg-266","Sg-267","Sg-268","Sg-269","Sg-270","Sg-271","Sg-272","Sg-273","Bh-260","Bh-261","Bh-262","Bh-263","Bh-264","Bh-265","Bh-266","Bh-267","Bh-268","Bh-269","Bh-270","Bh-271","Bh-272","Bh-273","Bh-274","Bh-275","Hs-263","Hs-264","Hs-265","Hs-266","Hs-267","Hs-268","Hs-269","Hs-270","Hs-271","Hs-272","Hs-273","Hs-274","Hs-275","Hs-276","Hs-277","Mt-265","Mt-266","Mt-267","Mt-268","Mt-269","Mt-270","Mt-271","Mt-272","Mt-273","Mt-274","Mt-275","Mt-276","Mt-277","Mt-278","Mt-279","Ds-267","Ds-268","Ds-269","Ds-270","Ds-271","Ds-272","Ds-273","Ds-274","Ds-275","Ds-276","Ds-277","Ds-278","Ds-279","Ds-280","Ds-281","Rg-272","Rg-273","Rg-274","Rg-275","Rg-276","Rg-277","Rg-278","Rg-279","Rg-280","Rg-281","Rg-282","Rg-283","Cn-277","Cn-278","Cn-279","Cn-280","Cn-281","Cn-282","Cn-283","Cn-284","Cn-285","Nh-283","Nh-284","Nh-285","Nh-286","Nh-287","Fl-285","Fl-286","Fl-287","Fl-288","Fl-289","Mc-287","Mc-288","Mc-289","Mc-290","Mc-291","Lv-289","Lv-290","Lv-291","Lv-292","Ts-291","Ts-292","Ts-293","Ts-294","Og-293"];
    var validIsotopes = true;
    var eles = document.querySelectorAll('[name^="measurement.results.isotope"]');
    for (var j=0; j<eles.length; j++){
        var validIsotope = false;

        // check if the value is in the list of valid isotopes
        for (var i=0; i<isotopes.length; i++){
            if (eles[j].value === isotopes[i]) {
                validIsotope = true;
            }
        }

        // if it's an update, the isotope can be empty if the "current" value exists (which it always will, but doesn't hurt to check)
        var existing_val_for_update = document.getElementsByName("current.measurement.results.isotope"+(j+1));
        if (eles[j].value === "" && existing_val_for_update !== null && existing_val_for_update !== "") {
            validIsotope = true;
        }

        var isotope_invalid_tooltip_text = document.getElementById("invalid-isotope"+(j+1)+"-tooltip-text");
        if (validIsotope) {
            isotope_invalid_tooltip_text.style.visibility = "hidden";
        } else {
            isotope_invalid_tooltip_text.style.visibility = "visible";
        }

        validIsotopes = validIsotopes && validIsotope;
    }
    
    document.getElementById('submit-record-button').disabled = !validIsotopes; //!(validIsotopes && validUnit);
    return validIsotopes;
}

function showHelp() {
    var help_div = document.getElementById("query-help");
    var display_mode = window.getComputedStyle(help_div).display;
    if (display_mode === "none") {
        help_div.style.display = "block";
    } else {
        help_div.style.display = "none";
    }
}
