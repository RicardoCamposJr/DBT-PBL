import './App.css';
import Bank from './components/Bank';
import NavBar from './components/NavBar';
import Transaction from './components/Transaction';

function App() {
  return (
    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
      <NavBar />
      <div style={{display: 'flex', justifyContent: 'center'}}>
        <div style={{width: '400px', padding: '50px'}}>
          <Bank label1={'User CPF'} label2={'Name'} botao={'Sign Up'}/>
        </div>
        <div style={{width: '400px', padding: '50px'}}>
          <Bank label1={'User CPF'} label2={'Value'} botao={'Deposit'}/>
        </div>
      </div>
      <div style={{width: '600px', padding: '50px'}}>
        <Transaction />
      </div>
    </div>
  );
}

export default App;
