export default function Bank({label1, label2, botao}) {
  return (
    <form>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">{label1}</label>
        <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp"/>
      </div>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">{label2}</label>
        <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp"/>
      </div>
      <button type="submit" class="btn btn-primary">{botao}</button>
    </form>
  )
}