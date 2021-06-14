document.querySelectorAll(".droparea__input").forEach(inputElement => {
	const dropareaElement = inputElement.closest(".droparea__input");
	dropareaElement.addEventListener("dragover", e => {
	//This listener is for when the user is holding an image over the drop area
		//e.preventDefault();
		console.log("Dragging over");
		dropareaElement.classList.add("droparea--over");
		dropareaElement.classList.remove("droparea__input");
	});

	["dragend", "dragleave"].forEach(type => {
		dropareaElement.addEventListener(type, e => {
		//This is for when a user either drags an image off the drop area, escapes out, or drops the file
		console.log("Dragged off or ended")
		    dropareaElement.classList.add("droparea__input");
			dropareaElement.classList.remove("droparea--over");
		});
	});

	dropareaElement.addEventListener("drop", e => {
	//This is for when the user drops the file
		//e.preventDefault();
		dropareaElement.classList.add("droparea__input");
		dropareaElement.classList.remove("droparea--over");
		file = e.dataTransfer.files[0];
		console.log("Dropped", file["name"])
	});
});
