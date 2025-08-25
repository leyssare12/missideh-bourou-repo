    $(document).ready(function() {
    const url = data('url');
    console.log(url);
    fetch(url)
      .then(response => response.json())
      .then(data => {
        const tbody = document.querySelector('#donnees-table tbody');
        data.forEach(item => {
          const row = document.createElement('tr');
          row.innerHTML = `
            <td>${item.montant_depense || '-'}</td>
            <td>${item.motif_depense || '-'}</td>
            <td>${item.date_depense || '-'}</td>
          `;
          tbody.appendChild(row);
        });
      });
    });