```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Innovative-Energie-Pullach-(IEP)" or company = "Innovative Energie Pullach (IEP)")
sort location, dt_announce desc
```
