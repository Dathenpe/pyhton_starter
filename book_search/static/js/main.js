document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('search-button').addEventListener('click', function() {
    const query = document.getElementById('search-query').value;
    const xhr = new XMLHttpRequest();

    xhr.open('GET', `/js-search?query=${encodeURIComponent(query)}`, true);

    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200){
        const response = JSON.parse(xhr.responseText);
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = ''; // Clear previous results

        if (response.length > 0){
          response.forEach(function(result) {
            const bookDiv = document.createElement('div');
            // Apply Tailwind classes to the main book container
            bookDiv.className = 'bg-white p-4 rounded-lg shadow-md mb-4 border border-gray-200';

            const bookName = document.createElement('h3');
            bookName.textContent = result.name;
            // Apply Tailwind classes to the book name
            bookName.className = 'text-xl font-bold text-indigo-700 mb-1';
            bookDiv.appendChild(bookName);

            const bookAuthor = document.createElement('p');
            bookAuthor.textContent = `Author: ${result.author}`;
            // Apply Tailwind classes to the book author
            bookAuthor.className = 'text-gray-600 text-sm italic mb-2';
            bookDiv.appendChild(bookAuthor);

            const bookDescription = document.createElement('p');
            bookDescription.textContent = result.description;
            // Apply Tailwind classes to the book description
            bookDescription.className = 'text-gray-800 text-base leading-relaxed mb-3';
            bookDiv.appendChild(bookDescription);

            const bookPrice  = document.createElement('p');
            bookPrice.textContent = `Price: $${result.price.toFixed(2)}`;
            // Apply Tailwind classes to the book price
            bookPrice.className = 'text-green-600 font-extrabold text-lg';
            bookDiv.appendChild(bookPrice);

            resultsDiv.appendChild(bookDiv);
          });
        } else {
          const noResults = document.createElement('p');
          noResults.textContent = 'No results found.';
          // Apply Tailwind classes for no results message
          noResults.className = 'text-center text-gray-500 text-lg p-6 bg-white rounded-lg shadow-sm';
          resultsDiv.appendChild(noResults);
        }
      } else if (xhr.readyState === 4){
        const errorMessage = document.createElement('p');
        errorMessage.textContent = `Error fetching results. Status: ${xhr.status}`;
        // Apply Tailwind classes for error message
        errorMessage.className = 'text-center text-red-600 font-semibold text-lg p-6 bg-white rounded-lg shadow-sm';
        resultsDiv.appendChild(errorMessage);
      }
    };
    xhr.send();
  });
});