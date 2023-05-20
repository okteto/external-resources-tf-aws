var data = [];

// Remove and complete icons in SVG format
var removeSVG = `
  <svg width="673" height="673" viewBox="0 0 673 673" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M336.667 0.333374C151.4 0.333374 0.679932 151.053 0.679932 336.307C0.679932 521.587 151.4 672.333 336.667 672.333C521.933 672.333 672.653 521.6 672.653 336.307C672.653 151.04 521.933 0.333374 336.667 0.333374ZM336.667 643.44C167.333 643.44 29.5733 505.68 29.5733 336.307C29.5733 166.987 167.347 29.2267 336.667 29.2267C506 29.2267 643.76 166.973 643.76 336.32C643.76 505.68 506 643.453 336.667 643.453V643.44Z" />
    <path d="M465.667 444.86L357.103 336.295L465.639 227.759C471.292 222.106 471.288 212.976 465.643 207.33C459.997 201.684 450.863 201.677 445.21 207.33L336.674 315.866L228.147 207.34C222.501 201.694 213.364 201.69 207.718 207.336C202.065 212.989 202.072 222.123 207.718 227.768L316.245 336.295L207.699 444.841C202.054 450.487 202.05 459.624 207.699 465.273C213.345 470.919 222.482 470.915 228.128 465.269L336.674 356.724L445.238 465.288C450.888 470.938 460.018 470.942 465.671 465.288C471.32 459.646 471.313 450.505 465.671 444.863L465.667 444.86Z" />
  </svg>
`


renderFoodList();

// User clicked on the add button
// If there is any text inside the item field, add that text to the food list
document.getElementById("add").addEventListener("click", function () {
  var value = document.getElementById("item").value;
  if (value) {
    addItem(value);
  }
});


document.getElementById("placeOrder").addEventListener("click", function () {
  const payload = {"items": data};
  fetch("/order",{
    method: "post",
    body: JSON.stringify(payload),
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
  }).then(response => {
    if (response.status >= 200 || response.status < 500) {
      $("#orderPlaced").addClass("modal-open");
    } else {
      console.log(`error ${response.status}`)  
    }
  }).catch(error => {
    console.log(error)
  })
});

document.querySelector("#orderPlaced").addEventListener("click", function () {
  closeModal();
});

$(document).keyup(function(e) {
  if (e.key === "Escape") {
    closeModal();
 }
});

const closeModal = () => {
  clearFoodList();
  $("#orderPlaced").removeClass("modal-open");
}

document.getElementById("item").addEventListener("keydown", function (e) {
  var value = this.value;
  if ((e.code === "Enter" || e.code === "NumpadEnter") && value) {
    addItem(value);
  }
});

function addItem(value) {
  const id = data.length;
  addItemToDOM(value, id);
  document.getElementById("item").value = "";

  data.push(value);
}

function renderFoodList() {
  if (!data.length) return;

  for (var i = 0; i < data.length; i++) {
    var value = data[i];
    var id = i;
    addItemToDOM(value, id);
  }
}

function clearFoodList() {
  if (!data.length) return;
  $('#food').empty();
  data = [];
}

function removeItem() {
  var item = this.parentNode;
  var parent = item.parentNode;
  var value = item.innerText;

  data.splice(data.indexOf(value), 1);
  parent.removeChild(item);
}

// Adds a new item to the fod list
function addItemToDOM(text, id) {
  var list = document.getElementById("food");
  var item = document.createElement("li");
  item.innerText = text;
  item.id = id;

  var remove = document.createElement("button");
  remove.classList.add("button-remove");
  remove.innerHTML = removeSVG;

  // Add click event for removing the item
  remove.addEventListener("click", removeItem);

  item.appendChild(remove);

  list.insertBefore(item, list.childNodes[0]);
}
