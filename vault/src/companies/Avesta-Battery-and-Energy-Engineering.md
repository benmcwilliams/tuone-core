```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Avesta-Battery-and-Energy-Engineering" or company = "Avesta Battery and Energy Engineering")
sort location, dt_announce desc
```
