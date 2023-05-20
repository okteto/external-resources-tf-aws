// Remove and complete icons in SVG format
var removeSVG =
  `
  <svg width="654" height="526" viewBox="0 0 654 526" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M653.333 502.507C653.333 508.694 650.875 514.632 646.5 519.007C642.125 523.382 636.187 525.84 630 525.84H23.3333C14.9948 525.84 7.292 521.392 3.12534 514.173C-1.04133 506.955 -1.04133 498.059 3.12534 490.84C7.292 483.621 14.9951 479.173 23.3333 479.173H630C636.187 479.173 642.125 481.632 646.5 486.007C650.875 490.382 653.333 496.319 653.333 502.507ZM0 432.507C0 275.707 68.5987 109.333 256.667 85.5333V67.804C256.729 50.0587 263.802 33.064 276.349 20.5173C288.896 7.97039 305.891 0.897322 323.636 0.834656H329.704H329.699C347.444 0.897156 364.439 7.97012 376.985 20.5173C389.532 33.0643 396.605 50.0587 396.668 67.804V85.5387C584.735 108.872 653.335 275.699 653.335 432.512V432.507C653.335 438.694 650.876 444.632 646.501 449.007C642.126 453.382 636.189 455.84 630.001 455.84H23.3345C17.1471 455.84 11.2095 453.382 6.83452 449.007C2.45959 444.632 0 438.694 0 432.507ZM303.333 82.5067H350V67.8093C350 62.4239 347.859 57.2624 344.052 53.4547C340.245 49.6473 335.083 47.5068 329.697 47.5068H323.63H323.635C318.249 47.5068 313.088 49.6475 309.28 53.4547C305.473 57.262 303.332 62.4235 303.332 67.8093L303.333 82.5067ZM46.6667 409.173H606.667C602.234 320.741 567 129.173 350 129.173H303.333C87.0267 129.173 51.8 320.747 46.6667 409.173Z" />
  </svg>
  `;

function removeItem() {
  var item = this.parentNode;
  var parent = item.parentNode;
  var value = item.innerText;
  var orderId = item.id.split("_").shift();
  const payload = { orderId: orderId, item: value };

  fetch("/ready", {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (response.status >= 200 || response.status < 500) {
        parent.removeChild(item);
      } else {
        console.log(`error ${response.status}`);
      }
    })
    .catch((error) => {
      console.log(error);
    });
}

// Adds a new item to the fod list
function addItemToDOM(orderId, name) {
  var list = document.getElementById("food");
  var item = document.createElement("li");
  item.innerText = name;
  item.id = orderId;

  var remove = document.createElement("button");
  remove.classList.add("button-remove");
  remove.innerHTML = removeSVG;

  // Add click event for removing the item
  remove.addEventListener("click", removeItem);

  item.appendChild(remove);

  list.insertBefore(item, list.childNodes[0]);
}

var backoff = 1;

function getOrders() {
  fetch("/orders", {
    method: "GET",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw Error(response.statusText);
      }
      return response.json()
    })
    .then(data => {
      backoff = 1;
      data.items.forEach((item, index) => {
        orderId = `${data.orderId}_${index}`;
        addItemToDOM(orderId, item.name);
      });
    })
    .catch((error) => {
      backoff++;
      console.log(error);
    })
    .finally(()=> {
      timeout = 1000 * backoff;
      setTimeout(timeout, getOrders());
    });
}

window.onload = getOrders;
