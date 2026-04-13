<template>
  <div class="container mt-4">
    <h2>Admin Dashboard</h2>

    <div class="row g-3 mb-4">
      <div class="col-md-3">
        <div class="card bg-light p-3 text-center">
          <h6 class="mb-1">Students</h6>
          <strong>{{ summary.students }}</strong>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card bg-light p-3 text-center">
          <h6 class="mb-1">Companies</h6>
          <strong>{{ summary.companies }}</strong>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card bg-light p-3 text-center">
          <h6 class="mb-1">Drives</h6>
          <strong>{{ summary.drives }}</strong>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card bg-light p-3 text-center">
          <h6 class="mb-1">Applications</h6>
          <strong>{{ summary.applications }}</strong>
        </div>
      </div>
    </div>

    <div v-if="message" class="alert alert-success">{{ message }}</div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <h4>Pending Approvals</h4>
    <div class="card">
      <div class="card-body">
        <div v-if="!pendingItems.length" class="text-muted">
          No pending approvals.
        </div>
        <table v-else class="table table-striped mb-0">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Details</th>
              <th class="text-end">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in pendingItems" :key="`${item.type}-${item.id}`">
              <td>{{ item.name }}</td>
              <td class="text-capitalize">{{ item.type }}</td>
              <td>{{ item.subtitle || "-" }}</td>
              <td class="text-end">
                <button
                  @click="approve(item.id, item.type)"
                  class="btn btn-sm btn-success me-2"
                >
                  Approve
                </button>
                <button
                  @click="reject(item.id, item.type)"
                  class="btn btn-sm btn-outline-danger"
                >
                  Reject
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <h4 class="mt-4">User Management</h4>
    <div class="card">
      <div class="card-body">
        <div class="row g-2 mb-3">
          <div class="col-md-3">
            <select
              v-model="searchType"
              class="form-select"
              @change="searchUsers"
            >
              <option value="student">Students</option>
              <option value="company">Companies</option>
            </select>
          </div>
          <div class="col-md-9">
            <input
              v-model="searchQuery"
              @input="searchUsers"
              class="form-control"
              placeholder="Search by name or email"
            />
          </div>
        </div>

        <div v-if="!users.length" class="text-muted">No users found.</div>
        <table v-else class="table table-striped mb-0">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Status</th>
              <th class="text-end">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="`${user.role}-${user.id}`">
              <td>{{ user.name }}</td>
              <td>{{ user.email }}</td>
              <td>
                <span
                  :class="user.is_blacklisted ? 'text-danger' : 'text-success'"
                >
                  {{ user.is_blacklisted ? "Blacklisted" : "Active" }}
                </span>
              </td>
              <td class="text-end">
                <button
                  @click="toggleBlacklist(user)"
                  :class="
                    user.is_blacklisted
                      ? 'btn btn-sm btn-outline-success'
                      : 'btn btn-sm btn-outline-danger'
                  "
                >
                  {{ user.is_blacklisted ? "Unblacklist" : "Blacklist" }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      summary: { students: 0, companies: 0, drives: 0, applications: 0 },
      pendingItems: [],
      searchType: "student",
      searchQuery: "",
      users: [],
      message: "",
      error: "",
    };
  },
  methods: {
    authHeaders() {
      return { Authorization: localStorage.getItem("token") };
    },
    async fetchSummary() {
      const res = await fetch("http://localhost:5000/api/admin/summary", {
        headers: this.authHeaders(),
      });
      this.summary = await res.json();
    },
    async fetchPending() {
      const res = await fetch("http://localhost:5000/api/admin/pending", {
        headers: this.authHeaders(),
      });
      this.pendingItems = await res.json();
    },
    async approve(id, type) {
      this.message = "";
      this.error = "";
      const res = await fetch(
        `http://localhost:5000/api/admin/approve/${type}/${id}`,
        {
          method: "POST",
          headers: this.authHeaders(),
        },
      );
      const data = await res.json();
      if (res.ok) {
        this.message = data.message;
        await this.refresh();
      } else {
        this.error = data.message || "Approval failed";
      }
    },
    async reject(id, type) {
      this.message = "";
      this.error = "";
      const res = await fetch(
        `http://localhost:5000/api/admin/reject/${type}/${id}`,
        {
          method: "POST",
          headers: this.authHeaders(),
        },
      );
      const data = await res.json();
      if (res.ok) {
        this.message = data.message;
        await this.refresh();
      } else {
        this.error = data.message || "Rejection failed";
      }
    },
    async refresh() {
      await Promise.all([
        this.fetchSummary(),
        this.fetchPending(),
        this.searchUsers(),
      ]);
    },
    async searchUsers() {
      const query = this.searchQuery
        ? `&q=${encodeURIComponent(this.searchQuery)}`
        : "";
      const res = await fetch(
        `http://localhost:5000/api/admin/users?type=${this.searchType}${query}`,
        {
          headers: this.authHeaders(),
        },
      );
      const data = await res.json();
      if (res.ok) {
        this.users = data;
      } else {
        this.users = [];
        this.error = data.message || "Failed to fetch users";
      }
    },
    async toggleBlacklist(user) {
      this.message = "";
      this.error = "";
      const shouldBlacklist = !user.is_blacklisted;
      const res = await fetch(
        `http://localhost:5000/api/admin/blacklist/${user.role}/${user.id}`,
        {
          method: "POST",
          headers: {
            ...this.authHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ blacklisted: shouldBlacklist }),
        },
      );
      const data = await res.json();
      if (res.ok) {
        this.message = data.message;
        await this.searchUsers();
      } else {
        this.error = data.message || "Failed to update blacklist";
      }
    },
  },
  mounted() {
    this.refresh();
  },
};
</script>
