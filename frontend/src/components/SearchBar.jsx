import { MagnifyingGlassIcon } from "@phosphor-icons/react";
import { motion } from "motion/react"


export default function SearchBar({ query, setQuery, onSubmit }) {
  return (
    <motion.form 
    initial={{ opacity: 0, y: -20 }}   
animate={{ opacity: 1, y: 0 }}     
transition={{ delay: 1.2 ,duration: 0.9, ease: "easeInOut" }}
    
    className="searchBox" onSubmit={onSubmit}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search query"
      />
      <button type="submit" className="search-btn btn btn-primary">
      <MagnifyingGlassIcon size={24}/>
      </button>
    </motion.form>
  );
}