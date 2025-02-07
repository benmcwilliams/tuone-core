```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Koncar-Generators-and-Motors" or company = "Koncar Generators and Motors")
sort location, dt_announce desc
```
