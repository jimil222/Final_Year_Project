import { Star, BookOpen, User, TrendingUp } from 'lucide-react';

const RecommendationCard = ({ book }) => {
  return (
    <div className="group bg-white rounded-xl shadow-sm hover:shadow-lg border border-gray-100 hover:border-blue-200 transition-all duration-200 p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="bg-yellow-100 p-2 rounded-lg">
            <Star className="text-yellow-600 w-5 h-5 fill-current" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 text-lg group-hover:text-blue-600 transition-colors">
              {book.title}
            </h3>
            <p className="text-gray-600 text-sm flex items-center gap-1">
              <User className="w-4 h-4" />
              {book.author}
            </p>
          </div>
        </div>
        <div className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          AI Pick
        </div>
      </div>

      <div className="flex items-center justify-between text-sm">
        <div className="text-gray-500 flex items-center gap-1">
          <BookOpen className="w-4 h-4" />
          ID: {book.book_id}
        </div>
        <div className="text-blue-600 font-medium">
          Recommended for you
        </div>
      </div>
    </div>
  );
};

export default RecommendationCard;

