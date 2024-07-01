export default function Transaction() {
  return (
    <form>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">User CPF</label>
        <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp"/>
      </div>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">Receiver CPF</label>
        <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp"/>
      </div>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">Transfer CPF</label>
        <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp"/>
      </div>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">Source Bank Id</label>
        <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp"/>
      </div>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">Destination Bank Id</label>
        <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp"/>
      </div>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">Amount</label>
        <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp"/>
      </div>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">Operation</label>
        <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp"/>
      </div>
      <button type="submit" class="btn btn-primary">Add operation</button>
      <button type="submit" class="btn btn-primary">Run Transaction Package</button>
    </form>
  )
}