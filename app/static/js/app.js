
async function getUserData(){
    const response = await fetch('/api/users');
    return response.json();
}

function loadTable(users){
    const table = document.querySelector('#result');
    const rows = users.map(user => `<tr>
            <td>${user.id}</td>
            <td>${user.username}</td>
        </tr>`).join('');
    table.innerHTML = rows;
}

async function main(){
    const users = await getUserData();
    loadTable(users);
}

main();