<template>
  <div class="container mt-4">
    <h2>Admin Management Console</h2>
    <div class="row mb-4">
      <div class="col-md-4"><div class="card bg-light p-3 text-center"><h5>Students</h5> 120</div></div>
      <div class="col-md-4"><div class="card bg-light p-3 text-center"><h5>Companies</h5> 15</div></div>
      <div class="col-md-4"><div class="card bg-light p-3 text-center"><h5>Drives</h5> 8</div></div>
    </div>

    <h4>Pending Approvals</h4>
    <table class="table table-striped border">
      <thead>
        <tr>
          <th>Entity Name</th>
          <th>Type</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in pendingItems" :key="item.id">
          <td>{{ item.name }}</td>
          <td>{{ item.type }}</td>
          <td>
            <button @click="approve(item.id, item.type)" class="btn btn-sm btn-success me-2">Approve</button>
            <button @click="reject(item.id, item.type)" class="btn btn-sm btn-danger">Reject</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  data() {
    return { pendingItems: [] };
  },
  methods: {
    async fetchPending() {
      const res = await fetch('http://localhost:5000/api/admin/pending', {
        headers: { 'Authorization': localStorage.getItem('token') }
      });
      this.pendingItems = await res.json();
    },
    async approve(id, type) {
      await fetch(`http://localhost:5000/api/admin/approve/${type}/${id}`, { 
        method: 'POST',
        headers: { 'Authorization': localStorage.getItem('token') }
      });
      this.fetchPending();
    }
  },
  mounted() { this.fetchPending(); }
}
</script>