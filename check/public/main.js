var data = [];

// Remove and complete icons in SVG format
var removeSVG = `
  <svg width="673" height="673" viewBox="0 0 673 673" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M336.667 0.333374C151.4 0.333374 0.679932 151.053 0.679932 336.307C0.679932 521.587 151.4 672.333 336.667 672.333C521.933 672.333 672.653 521.6 672.653 336.307C672.653 151.04 521.933 0.333374 336.667 0.333374ZM336.667 643.44C167.333 643.44 29.5733 505.68 29.5733 336.307C29.5733 166.987 167.347 29.2267 336.667 29.2267C506 29.2267 643.76 166.973 643.76 336.32C643.76 505.68 506 643.453 336.667 643.453V643.44Z" />
    <path d="M465.667 444.86L357.103 336.295L465.639 227.759C471.292 222.106 471.288 212.976 465.643 207.33C459.997 201.684 450.863 201.677 445.21 207.33L336.674 315.866L228.147 207.34C222.501 201.694 213.364 201.69 207.718 207.336C202.065 212.989 202.072 222.123 207.718 227.768L316.245 336.295L207.699 444.841C202.054 450.487 202.05 459.624 207.699 465.273C213.345 470.919 222.482 470.915 228.128 465.269L336.674 356.724L445.238 465.288C450.888 470.938 460.018 470.942 465.671 465.288C471.32 459.646 471.313 450.505 465.671 444.863L465.667 444.86Z" />
  </svg>
`

const downloadSVG = `
<svg width="727" height="657" viewBox="0 0 727 657" fill="none" xmlns="http://www.w3.org/2000/svg">
<path fill-rule="evenodd" clip-rule="evenodd" d="M224.839 341.36C219.746 335.584 218.074 327.548 220.444 320.22C222.808 312.892 228.86 307.355 236.37 305.647C243.875 303.933 251.73 306.308 257.037 311.892L355.48 419.427V22.1342C355.631 14.4363 359.823 7.38481 366.516 3.57681C373.209 -0.23052 381.412 -0.23052 388.104 3.57681C394.797 7.38415 398.99 14.4362 399.14 22.1342V419.427L497.583 311.892C502.875 306.23 510.765 303.793 518.323 305.49C525.88 307.188 531.974 312.766 534.334 320.146C536.688 327.527 534.959 335.6 529.782 341.365L393.408 490.325C389.278 494.851 383.434 497.429 377.31 497.429C371.179 497.429 365.336 494.851 361.211 490.325L224.839 341.36ZM704.746 391.751C698.954 391.756 693.408 394.058 689.314 398.152C685.22 402.245 682.918 407.798 682.918 413.589V612.696H44.4249V413.589C44.2739 405.886 40.0812 398.84 33.3885 395.032C26.6907 391.224 18.4872 391.224 11.7952 395.032C5.10253 398.839 0.909731 405.886 0.758798 413.589V634.469C0.75359 640.261 3.04519 645.818 7.14426 649.922C11.238 654.021 16.7953 656.323 22.5869 656.318H704.747C710.533 656.329 716.085 654.032 720.184 649.938C724.278 645.849 726.575 640.297 726.575 634.511V413.591C726.57 407.8 724.268 402.253 720.174 398.154C716.085 394.06 710.533 391.758 704.747 391.753L704.746 391.751Z" fill="black"/>
</svg>
`
renderChecks();

function renderChecks() {
fetch("/checks",{
    method: "get",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
  }).then(response => {
    if (response.status >= 200 || response.status < 500) {
      response.json()
      .then(json => {
        json.forEach(order => {
          console.log(`adding ${order.orderId} - ${order.total }`);
          addItemToDOM(order.orderId, order.total, order.items, order.url);
        })
      })
    } else {
      console.log(`error ${response.status}`)  
    }
  }).catch(error => { 
    console.log(error)
  })
}

function removeItem() {
  var item = this.parentNode.parentNode;
  var parent = item.parentNode;
  var orderId = item.id;

  fetch(`/checks/${orderId}`, {
    method: "DELETE",
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
function addItemToDOM(checkId, total, items, url) {
  var list = document.getElementById("check");
  var item = document.createElement("li");
  const food = items.map(i => i.name).join(", ");
  
  item.innerHTML = `
    <div>
      <dl>
        <dt>Check Id</dt>
        <dd>${checkId}</dd>
        <dt>Order</dt>
        <dd>${food}</dd>
        <dt>Total $</dt>
        <dd>${total}</dd>
      </dl>
      <a href="${url}" class="download-link">Download Receipt</a>
    </div>`;
  item.id = checkId;

  var buttons = document.createElement("div");
  buttons.classList.add("buttons");

  var remove = document.createElement("button");
  remove.classList.add("button-remove");
  remove.innerHTML = removeSVG;


  // Add click event for removing the item
  remove.addEventListener("click", removeItem);

  buttons.appendChild(remove);
  item.appendChild(buttons);

  list.insertBefore(item, list.childNodes[0]);
}