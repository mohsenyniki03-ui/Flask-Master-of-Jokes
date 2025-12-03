import React, { useEffect, useState } from 'react';
import axios from 'axios';

function UserCount() {
    const [count, setCount] = useState(null);

useEffect(() => {
    async function fetchCount() {
        try{
            const response = await axios.get('http://localhost:5000/api/status/jokes');
            setCount(response.data.count);
        } catch(err) {
            console.error('Error fetching user count:', err)
        }
    }

    fetchCount();
}, []);

return (
        <div>
        <h2>Total Users</h2>
        <p>{count !== null ? count : 'Loading...'}</p>
    </div>
);
}

export default UserCount;