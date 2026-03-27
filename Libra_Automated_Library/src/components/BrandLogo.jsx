import { GiOpenBook } from 'react-icons/gi';

const BrandLogo = ({ iconClassName = 'text-4xl', textClassName = 'text-3xl', stacked = false }) => {
  return (
    <div className={`inline-flex items-center ${stacked ? 'flex-col gap-2' : 'gap-2'}`}>
      <div className="p-2 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-md">
        <GiOpenBook className={iconClassName} />
      </div>
      <span
        className={`font-extrabold tracking-tight bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent ${textClassName}`}
      >
        Libra
      </span>
    </div>
  );
};

export default BrandLogo;